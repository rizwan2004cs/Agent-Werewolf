"""Load the single root-level .env (monorepo) before any module reads os.environ.

Importing anything from this package triggers this first, so OPENAI_API_KEY,
RPC_URL, PRIVATE_KEY, etc. from werewolf/.env are available everywhere. Falls
back silently if python-dotenv isn't installed (e.g. a bare mock run)."""
try:
    from pathlib import Path
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parents[2]  # werewolf/
    load_dotenv(_root / ".env")
    # Optional per-folder override, if someone still keeps orchestrator/.env.
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass
