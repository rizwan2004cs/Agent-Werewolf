"""Compile + deploy WerewolfArena.sol to the contract.dev stagenet.

Reads RPC_URL / CHAIN_ID / OPERATOR_KEY from backend/.env. Emits the ABI to
backend/abi.json and frontend/src/abi.json, deploys with the operator wallet,
then writes CONTRACT_ADDRESS into both .env files.

Usage:  python contract/deploy.py
"""
import json
import re
from pathlib import Path

from dotenv import dotenv_values
from solcx import compile_standard, install_solc
from web3 import Web3

ROOT = Path(__file__).resolve().parent.parent
SOL = ROOT / "contract" / "WerewolfArena.sol"
BACKEND_ENV = ROOT / "backend" / ".env"
FRONTEND_ENV = ROOT / "frontend" / ".env"
BACKEND_ABI = ROOT / "backend" / "abi.json"
FRONTEND_ABI = ROOT / "frontend" / "src" / "abi.json"
SOLC_VERSION = "0.8.20"


def compile_contract():
    install_solc(SOLC_VERSION)
    source = SOL.read_text()
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"WerewolfArena.sol": {"content": source}},
            "settings": {
                "optimizer": {"enabled": True, "runs": 200},
                "outputSelection": {
                    "*": {"*": ["abi", "evm.bytecode.object"]}
                },
            },
        },
        solc_version=SOLC_VERSION,
    )
    c = compiled["contracts"]["WerewolfArena.sol"]["WerewolfArena"]
    return c["abi"], c["evm"]["bytecode"]["object"]


def write_abi(abi):
    text = json.dumps(abi, indent=2)
    BACKEND_ABI.write_text(text)
    FRONTEND_ABI.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_ABI.write_text(text)
    print(f"  ABI -> {BACKEND_ABI}")
    print(f"  ABI -> {FRONTEND_ABI}")


def deploy(abi, bytecode, cfg):
    w3 = Web3(Web3.HTTPProvider(cfg["RPC_URL"]))
    if not w3.is_connected():
        raise SystemExit("Cannot reach RPC_URL")
    acct = w3.eth.account.from_key(cfg["OPERATOR_KEY"].strip())
    chain_id = int(cfg["CHAIN_ID"])
    print(f"  deployer: {acct.address}")
    print(f"  balance : {w3.from_wei(w3.eth.get_balance(acct.address), 'ether')} MON")

    Arena = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Arena.constructor().build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "chainId": chain_id,
            "gasPrice": w3.eth.gas_price,
        }
    )
    tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"  deploy tx: {h.hex()}  (waiting for receipt...)")
    rcpt = w3.eth.wait_for_transaction_receipt(h)
    print(f"  status   : {'OK' if rcpt.status == 1 else 'FAILED'}")
    return rcpt.contractAddress


def set_env(path: Path, key: str, value: str):
    text = path.read_text()
    if re.search(rf"^{key}=.*$", text, flags=re.MULTILINE):
        text = re.sub(rf"^{key}=.*$", f"{key}={value}", text, flags=re.MULTILINE)
    else:
        text += f"\n{key}={value}\n"
    path.write_text(text)
    print(f"  {key}={value}  -> {path}")


def main():
    cfg = dotenv_values(BACKEND_ENV)
    for req in ("RPC_URL", "CHAIN_ID", "OPERATOR_KEY"):
        if not cfg.get(req):
            raise SystemExit(f"Missing {req} in {BACKEND_ENV}")

    print("Compiling…")
    abi, bytecode = compile_contract()
    write_abi(abi)

    print("Deploying…")
    address = deploy(abi, bytecode, cfg)
    print(f"\nDeployed WerewolfArena at: {address}\n")

    print("Updating .env files…")
    set_env(BACKEND_ENV, "CONTRACT_ADDRESS", address)
    set_env(FRONTEND_ENV, "VITE_CONTRACT_ADDRESS", address)
    set_env(FRONTEND_ENV, "VITE_CHAIN_ID", cfg["CHAIN_ID"])
    set_env(FRONTEND_ENV, "VITE_RPC_URL", cfg["RPC_URL"])
    print("\nDone.")


if __name__ == "__main__":
    main()
