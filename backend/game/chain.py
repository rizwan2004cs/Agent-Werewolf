"""web3 bridge — operator-driven. MOCK_CHAIN=1 (default) logs every call and
returns fakes so the whole game runs offline. Set MOCK_CHAIN=0 + GAME_CONTRACT +
BETTING_CONTRACT + PRIVATE_KEY to write to the live contracts (contract.dev
stagenet, chainId 143).

Two contracts, all writes signed by ONE operator key:
  AgentWerewolf — immutable game record: role-hash commit, kills, votes, winner
  WerewolfArena — parimutuel betting: operator opens/freezes/resolves; users bet
"""
from __future__ import annotations

import os
import json
import threading
from pathlib import Path

MOCK_CHAIN = os.environ.get("MOCK_CHAIN", "1") == "1"
_OPERATOR_KEY = os.environ.get("ORCHESTRATOR_KEY") or os.environ.get("PRIVATE_KEY") or ""
_ABI_DIR = Path(__file__).resolve().parents[2] / "shared" / "abi"

w3 = None
game = None
arena = None
_acct = None
_CHAIN_ID = 0
_mock_market_counter = 0

if not MOCK_CHAIN:
    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(os.environ["RPC_URL"]))
    _CHAIN_ID = int(os.environ.get("CHAIN_ID", "143"))
    _acct = w3.eth.account.from_key(_OPERATOR_KEY)
    with open(_ABI_DIR / "AgentWerewolf.json") as f:
        _game_abi = json.load(f)["abi"]
    with open(_ABI_DIR / "WerewolfArena.json") as f:
        _arena_abi = json.load(f)["abi"]
    game = w3.eth.contract(address=Web3.to_checksum_address(os.environ["GAME_CONTRACT"]), abi=_game_abi)
    arena = w3.eth.contract(address=Web3.to_checksum_address(os.environ["BETTING_CONTRACT"]), abi=_arena_abi)


def _log(msg: str):
    print(f"[chain{' MOCK' if MOCK_CHAIN else ''}] {msg}")


def role_hash(role_enum: int, idx: int, salt_hex: str) -> bytes:
    """keccak256(abi.encodePacked(uint8 role, uint8 idx, bytes32 salt))."""
    if MOCK_CHAIN:
        return b"\x00" * 32
    from web3 import Web3

    salt = bytes.fromhex(salt_hex[2:] if salt_hex.startswith("0x") else salt_hex)
    return Web3.keccak(bytes([role_enum, idx]) + salt)


# All operator txs come from ONE key, so they must go out one at a time with
# strictly increasing nonces. The game thread (freeze/resolve) and the API
# thread (sponsored /bet) both send txs — without this lock they collide.
# (Ported from clean-branch chain/client.py.)
_tx_lock = threading.Lock()
_next_nonce: int | None = None


def _broadcast(build_tx):
    """build_tx(nonce) -> tx hash. Serialized, nonce-tracked, one retry."""
    global _next_nonce
    with _tx_lock:
        chain_nonce = w3.eth.get_transaction_count(_acct.address, "pending")
        if _next_nonce is None or chain_nonce > _next_nonce:
            _next_nonce = chain_nonce
        nonce = _next_nonce
        try:
            h = build_tx(nonce)
        except Exception:
            # Resync from chain and retry once (stale/colliding nonce).
            nonce = w3.eth.get_transaction_count(_acct.address, "pending")
            h = build_tx(nonce)
        _next_nonce = nonce + 1
    return w3.eth.wait_for_transaction_receipt(h)


def _send(fn, value: int = 0):
    def build(nonce):
        tx = fn.build_transaction({
            "from": _acct.address,
            "nonce": nonce,
            "value": value,
            "chainId": _CHAIN_ID,
            "gasPrice": w3.eth.gas_price,
        })
        try:
            tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.25)
        except Exception:
            tx["gas"] = 600000
        signed = _acct.sign_transaction(tx)
        return w3.eth.send_raw_transaction(signed.raw_transaction)

    return _broadcast(build)


# ------------------------------------------------------ game (immutable log) --

def create_game(role_hashes) -> int:
    _log(f"createGame({len(role_hashes)} role commitments)")
    if MOCK_CHAIN:
        return 0
    rc = _send(game.functions.createGame(role_hashes))
    ev = game.events.GameCreated().process_receipt(rc)
    return ev[0]["args"]["gameId"]


def record_kill(game_id: int, victim_idx: int):
    _log(f"recordKill(game={game_id}, victim={victim_idx})")
    if MOCK_CHAIN:
        return None
    return _send(game.functions.recordKill(game_id, victim_idx))


def record_vote(game_id: int, voter_idx: int, target_idx: int):
    _log(f"recordVote(game={game_id}, voter={voter_idx} -> {target_idx})")
    if MOCK_CHAIN:
        return None
    return _send(game.functions.recordVote(game_id, voter_idx, target_idx))


def declare_winner(game_id: int, team_enum: int):
    _log(f"declareWinner(game={game_id}, team={team_enum})")
    if MOCK_CHAIN:
        return None
    return _send(game.functions.declareWinner(game_id, team_enum))


# ------------------------------------------------------------ betting (arena) -

def open_market(game_id: int, num_options: int) -> int:
    global _mock_market_counter
    _log(f"openMarket(game={game_id}, options={num_options})")
    if MOCK_CHAIN:
        mid = _mock_market_counter
        _mock_market_counter += 1
        return mid
    _send(arena.functions.openMarket(game_id, num_options))
    return arena.functions.marketCount().call() - 1


def freeze_market(market_id: int):
    _log(f"freezeMarket(market={market_id})")
    if MOCK_CHAIN:
        return None
    return _send(arena.functions.freezeMarket(market_id))


def resolve_market(market_id: int, winning_option_idx: int):
    _log(f"resolveMarket(market={market_id}, winner={winning_option_idx})")
    if MOCK_CHAIN:
        return None
    return _send(arena.functions.resolveMarket(market_id, winning_option_idx))


def get_pools(market_id: int):
    """Live per-option pools in MON (strings), or None in mock mode."""
    if MOCK_CHAIN:
        return None
    from web3 import Web3

    raw = arena.functions.getPools(market_id).call()
    return [str(Web3.from_wei(x, "ether")) for x in raw]


def place_bet(market_id: int, option_idx: int, amount_mon: str):
    """House-sponsored bet: the OPERATOR wallet stakes on behalf of a user, so
    bettors need no MON and sign nothing. Off-chain bookkeeping (loop.py) tracks
    whose bet it is; payouts go out via send_mon on resolution."""
    _log(f"placeBet(market={market_id}, option={option_idx}, {amount_mon} MON, sponsored)")
    if MOCK_CHAIN:
        return None
    from web3 import Web3

    return _send(arena.functions.placeBet(market_id, option_idx),
                 value=Web3.to_wei(amount_mon, "ether"))


def send_mon(to_address: str, amount_mon: str):
    """Direct MON transfer from the operator wallet (sponsored payout). Returns tx hash hex."""
    _log(f"sendMON({amount_mon} -> {to_address})")
    if MOCK_CHAIN:
        return None
    from web3 import Web3

    sent_hash = {}

    def build(nonce):
        tx = {
            "from": _acct.address,
            "to": Web3.to_checksum_address(to_address),
            "value": Web3.to_wei(amount_mon, "ether"),
            "nonce": nonce,
            "chainId": _CHAIN_ID,
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
        }
        signed = _acct.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signed.raw_transaction)
        sent_hash["h"] = h
        return h

    _broadcast(build)
    return sent_hash["h"].hex()
