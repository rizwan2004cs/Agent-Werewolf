"""GameState -> client JSON, with server-side fog of war.

The ONLY place game state crosses to a client. Shapes match docs/02-INTERFACES
exactly. Fog rules are mandatory and enforced here, never on the client:
  - mode=bettor: hide role unless revealed; omit privateReasoning.
  - mode=god:    return everything.
"""
from .config import config
from .state import GameState


def _player(p, mode: str) -> dict:
    role = p.role if (mode == "god" or p.revealed_role) else None
    return {
        "idx": p.idx,
        "name": p.name,
        "avatarSeed": p.name,
        "alive": p.alive,
        "role": role,
        "revealedRole": p.revealed_role,
        "currentSpeech": p.current_speech,
    }


def _market(m) -> dict:
    return {
        "marketId": m.market_id,
        "type": m.type,
        "round": m.round,
        "options": m.options,
        "pools": m.pools,
        "frozen": m.frozen,
        "resolved": m.resolved,
        "winningOption": m.winning_option,
    }


def to_client(state: GameState, mode: str = "bettor") -> dict:
    out = {
        "gameId": state.game_id,
        "phase": state.phase,
        "round": state.round,
        "maxRounds": state.max_rounds,
        "pot": state.pot,
        "speakingIdx": state.speaking_idx,
        "players": [_player(p, mode) for p in state.players],
        "nightResult": state.night_result,
        "discussionLog": state.discussion_log,
        "votes": state.votes,
        "bettingOpen": state.betting_open,
        "markets": [_market(m) for m in state.markets],
        "winner": state.winner,
        "agentProvider": "mock" if config.use_mock else config.openai_model,
    }
    if mode == "god":
        out["privateReasoning"] = state.private_reasoning
    return out
