"""Runtime configuration — the single place that reads the environment.

Nothing else in the codebase should touch os.environ. Import `config` and read
attributes. `.env` is loaded here if python-dotenv is available.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Single root .env (repo root, gitignored) is the source of truth;
    # also honour a local backend/.env and plain process env.
    _ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
    if _ROOT_ENV.exists():
        load_dotenv(_ROOT_ENV)
    load_dotenv()
except Exception:
    pass


def _env(*names: str, default: str = "") -> str:
    """First non-empty value among aliases (new name first, legacy fallback)."""
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    return default


class Config:
    def __init__(self):
        # --- LLM (OpenAI) ---
        self.openai_api_key: str = os.environ.get("OPENAI_API_KEY", "").strip()
        self.openai_model: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        # No key => keyless mock mode (canned agents, no cost).
        self.use_mock: bool = not bool(self.openai_api_key)

        # --- Pacing --- (PACE=0 runs instantly; >1 slows the "beats")
        self.pace: float = float(_env("PACE", "PACE_SECONDS", default="2.0"))

        # --- Chain (contract.dev stagenet; wired at Milestone 5) ---
        self.rpc_url: str = _env("RPC_URL")
        self.chain_id: str = _env("CHAIN_ID")
        self.contract_address: str = _env("CONTRACT_ADDRESS", "GAME_CONTRACT")
        self.betting_address: str = _env("BETTING_CONTRACT")
        self.operator_key: str = _env("OPERATOR_KEY", "PRIVATE_KEY")
        # MOCK_CHAIN=1 forces chain writes off even if RPC vars are set.
        if os.environ.get("MOCK_CHAIN", "").strip() == "1":
            self.rpc_url = ""

    @property
    def llm_mode(self) -> str:
        return "MOCK" if self.use_mock else f"OPENAI:{self.openai_model}"


config = Config()
