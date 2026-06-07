"""Raw chain port — real web3.py implementation (Milestone 5).

Talks to the deployed WerewolfArena on the contract.dev stagenet using the
operator wallet. Function signatures are identical to the old stub, so
chain/markets.py (which wraps every call in try/except) is unchanged.

Operator txs are serialized behind a lock with an in-process nonce tracker:
all operator writes come from one key, so they MUST go out one at a time with
strictly increasing nonces. The tracker resyncs from the chain and retries once
on a nonce error (e.g. after a restart left a pending tx).

Web3 + contract are initialised lazily: importing this module never requires a
configured chain, so mock/off-chain runs still work.
"""
import json
import threading
from pathlib import Path

from ..config import config

_ABI_PATH = Path(__file__).resolve().parents[2] / "abi.json"

_w3 = None
_acct = None
_arena = None

_tx_lock = threading.Lock()
_next_nonce: int | None = None


def _ensure():
    """Lazily build the web3 client + contract handle (raises if unconfigured)."""
    global _w3, _acct, _arena
    if _arena is not None:
        return
    if not (config.rpc_url and config.contract_address and config.operator_key):
        raise RuntimeError("chain not configured (RPC_URL/CONTRACT_ADDRESS/OPERATOR_KEY)")
    from web3 import Web3

    _w3 = Web3(Web3.HTTPProvider(config.rpc_url))
    _acct = _w3.eth.account.from_key(config.operator_key.strip())
    abi = json.loads(_ABI_PATH.read_text())
    _arena = _w3.eth.contract(
        address=Web3.to_checksum_address(config.contract_address), abi=abi
    )


def _build_and_send(fn, nonce: int):
    tx = fn.build_transaction(
        {
            "from": _acct.address,
            "nonce": nonce,
            "chainId": int(config.chain_id),
            "gasPrice": _w3.eth.gas_price,
        }
    )
    try:
        tx["gas"] = int(_w3.eth.estimate_gas(tx) * 1.25)
    except Exception:
        tx["gas"] = 400000
    signed = _acct.sign_transaction(tx)
    return _w3.eth.send_raw_transaction(signed.raw_transaction)


def _send(fn):
    """Build, sign, broadcast an operator tx (serialized) and wait for receipt."""
    global _next_nonce
    with _tx_lock:
        chain_nonce = _w3.eth.get_transaction_count(_acct.address, "pending")
        if _next_nonce is None or chain_nonce > _next_nonce:
            _next_nonce = chain_nonce
        nonce = _next_nonce
        try:
            h = _build_and_send(fn, nonce)
        except Exception:
            # Resync from chain and retry once (handles stale/colliding nonce).
            nonce = _w3.eth.get_transaction_count(_acct.address, "pending")
            h = _build_and_send(fn, nonce)
        _next_nonce = nonce + 1
    # Bound the wait so a tx that never mines can't freeze the game loop
    # (markets.py wraps this in try/except and continues on timeout).
    return _w3.eth.wait_for_transaction_receipt(h, timeout=60)


def open_market(game_id: int, num_options: int) -> int:
    _ensure()
    _send(_arena.functions.openMarket(int(game_id), int(num_options)))
    # marketId == marketCount - 1 after the tx.
    return _arena.functions.marketCount().call() - 1


def freeze_market(market_id: int) -> None:
    _ensure()
    _send(_arena.functions.freezeMarket(int(market_id)))


def resolve_market(market_id: int, winning_idx: int) -> None:
    _ensure()
    _send(_arena.functions.resolveMarket(int(market_id), int(winning_idx)))


def get_pools(market_id: int) -> list[str]:
    """MON-per-option as strings (view call, no gas)."""
    _ensure()
    from web3 import Web3

    raw = _arena.functions.getPools(int(market_id)).call()
    return [str(Web3.from_wei(x, "ether")) for x in raw]
