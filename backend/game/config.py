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
# Smaller, separate-quota model tried automatically when the primary one fails
# (e.g. the big model's daily token cap is exhausted) before giving up to mock.
_DEFAULT_GROQ_FALLBACK = "llama-3.1-8b-instant"


class Config:
    def __init__(self):
        # --- LLM ---
        # Build an ordered fallback CHAIN of endpoints (all OpenAI-compatible).
        # Each call tries them in order; on failure (e.g. a rate-limit / daily
        # cap) it drops to the next, and only after all fail does it use mock.
        #
        # Default order favours the free provider first, paid as a safety net:
        #   1. Groq primary  (free, daily token cap)         GROQ_MODEL
        #   2. Groq fallback (smaller, separate quota)        GROQ_FALLBACK_MODEL
        #   3. OpenAI        (paid, reliable, no daily cap)    OPENAI_MODEL
        # Set LLM_PREFER=openai to put OpenAI first instead. No keys -> mock.
        openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
        groq_key = os.environ.get("GROQ_API_KEY", "").strip()
        env_model = (
            os.environ.get("OPENAI_MODEL") or os.environ.get("AGENT_MODEL") or ""
        ).strip()
        openai_base = os.environ.get("OPENAI_BASE_URL", "").strip()
        prefer = os.environ.get("LLM_PREFER", "").strip().lower()

        groq_chain: list[dict] = []
        if groq_key:
            groq_base = openai_base or GROQ_BASE_URL
            groq_primary = (
                os.environ.get("GROQ_MODEL", "").strip() or env_model or _DEFAULT_GROQ_MODEL
            )
            groq_fb = os.environ.get("GROQ_FALLBACK_MODEL", "").strip() or _DEFAULT_GROQ_FALLBACK
            groq_chain.append({"provider": "groq", "model": groq_primary, "api_key": groq_key, "base_url": groq_base})
            if groq_fb and groq_fb != groq_primary:
                groq_chain.append({"provider": "groq", "model": groq_fb, "api_key": groq_key, "base_url": groq_base})

        openai_chain: list[dict] = []
        if openai_key:
            openai_chain.append({"provider": "openai", "model": env_model or "gpt-4o-mini", "api_key": openai_key, "base_url": openai_base})

        # Order the two provider chains. OpenAI-first only if explicitly asked
        # (or if Groq isn't configured); otherwise Groq leads to save cost.
        if prefer == "openai" or not groq_chain:
            self.models: list[dict] = openai_chain + groq_chain
        else:
            self.models = groq_chain + openai_chain

        self.use_mock: bool = not self.models

        primary = self.models[0] if self.models else {"provider": "mock", "model": env_model or "gpt-4o-mini", "api_key": "", "base_url": ""}
        self.provider: str = primary["provider"]
        self.model: str = primary["model"]
        self.api_key: str = primary["api_key"]
        self.base_url: str = primary["base_url"]

        # Back-compat aliases (older code / tooling referenced these names).
        self.openai_api_key = self.api_key
        self.openai_model = self.model

        # --- Pacing --- (PACE=0 runs instantly; >1 slows the "beats")
        self.pace: float = float(os.environ.get("PACE", "1.0"))

    @property
    def llm_mode(self) -> str:
        if self.use_mock:
            return "MOCK"
        chain = " -> ".join(f"{m['provider']}:{m['model']}" for m in self.models)
        return chain


config = Config()
