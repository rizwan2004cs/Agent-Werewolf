"""Chain subsystem — the betting port. Engine talks to `markets`; `client` is
the swappable transport (stub now, web3.py at Milestone 5)."""
from . import markets

__all__ = ["markets"]
