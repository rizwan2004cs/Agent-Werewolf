"""Runtime configuration — the single place that reads the environment.

Nothing else in the codebase should touch os.environ. Import `config` and read
attributes. `.env` is loaded here if python-dotenv is available.
"""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


class Config:
    def __init__(self):
        # --- LLM (OpenAI) ---
        self.openai_api_key: str = os.environ.get("OPENAI_API_KEY", "").strip()
        self.openai_model: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        # No key => keyless mock mode (canned agents, no cost).
        self.use_mock: bool = not bool(self.openai_api_key)

        # --- Pacing --- (PACE=0 runs instantly; >1 slows the "beats")
        self.pace: float = float(os.environ.get("PACE", "1.0"))

        # --- Chain (contract.dev stagenet; wired at Milestone 5) ---
        self.rpc_url: str = os.environ.get("RPC_URL", "")
        self.chain_id: str = os.environ.get("CHAIN_ID", "")
        self.contract_address: str = os.environ.get("CONTRACT_ADDRESS", "")
        self.operator_key: str = os.environ.get("OPERATOR_KEY", "")

    @property
    def llm_mode(self) -> str:
        return "MOCK" if self.use_mock else f"OPENAI:{self.openai_model}"


config = Config()
