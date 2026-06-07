"""Game history persistence — JSON file on disk (ported from clean-branch).

Records each completed game (winner, roles, discussion, votes, market pools,
sponsored payouts) so past matches survive restarts and /history can serve them.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "data"
_FILE = _DATA / "history.json"


def load() -> list[dict]:
    if _FILE.exists():
        try:
            return json.loads(_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def next_game_id() -> int:
    games = load()
    return max((g.get("gameId", 0) for g in games), default=0) + 1


def record(state) -> None:
    """Append a completed game's summary. Best-effort; never raises."""
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        games = load()
        games.append({
            "gameId": state.game_id,
            "winner": state.winner,
            "rounds": state.round,
            "endedAt": int(time.time()),
            "players": [{"name": p.name, "role": p.role} for p in state.players],
            "discussionLog": state.discussion_log,
            "votes": state.votes,
            "markets": [{
                "marketId": m.market_id,
                "type": m.type,
                "round": m.round,
                "options": m.options,
                "winningOption": m.winning_option,
                "pools": m.pools,
            } for m in state.markets],
            "payouts": state.payouts,
        })
        _FILE.write_text(json.dumps(games, indent=2))
    except Exception as e:  # persistence must never break the game
        print(f"[history] failed to record game: {e}")
