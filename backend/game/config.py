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


GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


class Config:
    def __init__(self):
        # --- LLM ---
        # Provider auto-detect (both use the OpenAI-compatible API):
        #   OPENAI_API_KEY set -> OpenAI (or any OPENAI_BASE_URL endpoint)
        #   GROQ_API_KEY set   -> Groq (base_url defaults to Groq's endpoint)
        #   neither set        -> deterministic mock mode (canned agents, no cost)
        openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
        groq_key = os.environ.get("GROQ_API_KEY", "").strip()
        env_model = (
            os.environ.get("OPENAI_MODEL") or os.environ.get("AGENT_MODEL") or ""
        ).strip()

        if openai_key:
            self.provider: str = "openai"
            self.api_key: str = openai_key
            self.base_url: str = os.environ.get("OPENAI_BASE_URL", "").strip()
            self.model: str = env_model or "gpt-4o-mini"
        elif groq_key:
            self.provider = "groq"
            self.api_key = groq_key
            self.base_url = os.environ.get("OPENAI_BASE_URL", "").strip() or GROQ_BASE_URL
            self.model = (
                os.environ.get("GROQ_MODEL", "").strip()
                or env_model
                or _DEFAULT_GROQ_MODEL
            )
        else:
            self.provider = "mock"
            self.api_key = ""
            self.base_url = ""
            self.model = env_model or "gpt-4o-mini"

        self.use_mock: bool = self.provider == "mock"

        # Back-compat aliases (older code / tooling referenced these names).
        self.openai_api_key = self.api_key
        self.openai_model = self.model

        # --- Pacing --- (PACE=0 runs instantly; >1 slows the "beats")
        self.pace: float = float(os.environ.get("PACE", "1.0"))

    @property
    def llm_mode(self) -> str:
        return "MOCK" if self.use_mock else f"{self.provider.upper()}:{self.model}"


config = Config()
