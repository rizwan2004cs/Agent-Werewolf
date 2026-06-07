"""web3 bridge to the AgentWerewolf + WerewolfBetting contracts.

Runs in MOCK_CHAIN mode by default: every call is logged and returns a fake
receipt so the whole game loop runs locally without a funded wallet. Set
MOCK_CHAIN=0 and fill orchestrator/.env to talk to Monad testnet for real.
"""
from __future__ import annotations

import os
import json
import secrets
from pathlib import Path

MOCK_CHAIN = os.environ.get("MOCK_CHAIN", "1") == "1"

_ABI_DIR = Path(__file__).resolve().parents[2] / "shared" / "abi"

# --------------------------------------------------------------------- setup --

w3 = None
game = None
betting = None

if not MOCK_CHAIN:
    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(os.environ["RPC_URL"]))
    with open(_ABI_DIR / "AgentWerewolf.json") as f:
        game_abi = json.load(f)["abi"]
    with open(_ABI_DIR / "WerewolfBetting.json") as f:
        bet_abi = json.load(f)["abi"]
    game = w3.eth.contract(address=os.environ["GAME_CONTRACT"], abi=game_abi)
    betting = w3.eth.contract(address=os.environ["BETTING_CONTRACT"], abi=bet_abi)


# ----------------------------------------------------------------- utilities --

def role_hash(role_enum: int, idx: int, salt_hex: str) -> bytes:
    """keccak256(abi.encodePacked(uint8 role, uint8 idx, bytes32 salt))."""
    if MOCK_CHAIN:
        return b"\x00" * 32
    from web3 import Web3

    salt = bytes.fromhex(salt_hex[2:] if salt_hex.startswith("0x") else salt_hex)
    packed = bytes([role_enum, idx]) + salt
    return Web3.keccak(packed)


def new_agent_wallets(n: int) -> list[dict]:
    """Return n {address, key} dicts. Mock uses deterministic fakes; real mode
    generates fresh keys (fund each from the faucet for a live demo)."""
    if MOCK_CHAIN:
        return [
            {"address": "0x" + f"{(i + 1):040x}", "key": "0x" + f"{(i + 1):064x}"}
            for i in range(n)
        ]
    from eth_account import Account

    wallets = []
    for _ in range(n):
        key = "0x" + secrets.token_hex(32)
        wallets.append({"address": Account.from_key(key).address, "key": key})
    return wallets


def _send(fn, signer_key: str, value: int = 0):
    acct = w3.eth.account.from_key(signer_key)
    tx = fn.build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "value": value,
            "chainId": int(os.environ["CHAIN_ID"]),
            "gas": 600000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(h)


def _log(msg: str):
    print(f"[chain{' MOCK' if MOCK_CHAIN else ''}] {msg}")


# ------------------------------------------------------------------- game ----

def create_game(player_addrs, role_hashes, pot_wei, deployer_key):
    _log(f"createGame({len(player_addrs)} players, pot={pot_wei} wei)")
    if MOCK_CHAIN:
        return 0  # gameId
    rc = _send(game.functions.createGame(player_addrs, role_hashes), deployer_key, value=pot_wei)
    return _read_game_id(rc)


def commit_night_kill(game_id, kill_hash, key):
    _log(f"commitNightKill(game={game_id})")
    if MOCK_CHAIN:
        return None
    return _send(game.functions.commitNightKill(game_id, kill_hash), key)


def reveal_night_kill(game_id, victim_idx, salt_hex, key):
    _log(f"revealNightKill(game={game_id}, victim={victim_idx})")
    if MOCK_CHAIN:
        return None
    salt = bytes.fromhex(salt_hex[2:])
    return _send(game.functions.revealNightKill(game_id, victim_idx, salt), key)


def reveal_role(game_id, idx, role_enum, salt_hex, key):
    _log(f"revealRole(game={game_id}, idx={idx}, role={role_enum})")
    if MOCK_CHAIN:
        return None
    salt = bytes.fromhex(salt_hex[2:])
    return _send(game.functions.revealRole(game_id, idx, role_enum, salt), key)


def submit_vote(game_id, target_idx, agent_key):
    _log(f"submitVote(game={game_id}, target={target_idx})")
    if MOCK_CHAIN:
        return None
    return _send(game.functions.submitVote(game_id, target_idx), agent_key)


def resolve_vote(game_id, key):
    _log(f"resolveVote(game={game_id})")
    if MOCK_CHAIN:
        return None
    return _send(game.functions.resolveVote(game_id), key)


def declare_winner(game_id, team_enum, key):
    _log(f"declareWinner(game={game_id}, team={team_enum})")
    if MOCK_CHAIN:
        return None
    return _send(game.functions.declareWinner(game_id, team_enum), key)


# ----------------------------------------------------------------- betting ---

def open_market(game_id, market_type, num_options, key):
    _log(f"openMarket(game={game_id}, type={market_type}, options={num_options})")
    if MOCK_CHAIN:
        return None  # marketId tracked in orchestrator state for the demo
    rc = _send(betting.functions.openMarket(game_id, market_type, num_options), key)
    return rc


def freeze_market(market_id, key):
    _log(f"freezeMarket(market={market_id})")
    if MOCK_CHAIN:
        return None
    return _send(betting.functions.freezeMarket(market_id), key)


def resolve_market(market_id, winning_option_idx, key):
    _log(f"resolveMarket(market={market_id}, winner={winning_option_idx})")
    if MOCK_CHAIN:
        return None
    return _send(betting.functions.resolveMarket(market_id, winning_option_idx), key)


# ------------------------------------------------------------------ helpers --

def _read_game_id(receipt) -> int:
    ev = game.events.GameCreated().process_receipt(receipt)
    return ev[0]["args"]["gameId"]
