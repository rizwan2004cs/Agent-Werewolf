"""GameState -> client JSON, with server-side fog of war.

The ONLY place game state crosses to a client. Fog rules are mandatory and
enforced here, never on the client:
  - mode=god:    return everything (spectator).
  - mode=bettor: hide role unless revealed; omit privateReasoning.
  - mode=player: like bettor, but reveal the HUMAN player's OWN role + secret
                 knowledge (so they can play), and surface `awaiting`/`you`.
"""
from .config import config
from .state import GameState


def _player(p, mode: str, human_idx: int | None) -> dict:
    show = (
        mode == "god"
        or p.revealed_role is not None
        or (mode == "player" and p.idx == human_idx)
    )
    return {
        "idx": p.idx,
        "name": p.name,
        "avatarSeed": p.name,
        "alive": p.alive,
        "role": p.role if show else None,
        "revealedRole": p.revealed_role,
        "currentSpeech": p.current_speech,
        "isHuman": p.is_human,
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


def _you(state: GameState) -> dict | None:
    """The human player's private view of themselves (role + secret)."""
    h = state.human_player()
    if not h:
        return None
    you = {"idx": h.idx, "name": h.name, "role": h.role, "alive": h.alive}
    if h.role == "seer" and state.seer_knowledge:
        you["seer"] = state.seer_knowledge
    if h.role == "wolf":
        partner = next(
            (w.name for w in state.wolves() if w.idx != h.idx), None
        )
        you["partner"] = partner
    return you


def to_client(state: GameState, mode: str = "bettor") -> dict:
    human_idx = state.human_player().idx if state.human_player() else None
    out = {
        "gameId": state.game_id,
        "kind": state.kind,
        "phase": state.phase,
        "round": state.round,
        "maxRounds": state.max_rounds,
        "pot": state.pot,
        "speakingIdx": state.speaking_idx,
        "speechKind": state.speech_kind,
        "players": [_player(p, mode, human_idx) for p in state.players],
        "nightResult": state.night_result,
        "discussionLog": state.discussion_log,
        "votes": state.votes,
        "bettingOpen": state.betting_open,
        "markets": [_market(m) for m in state.markets],
        "payouts": state.payouts,
        "winner": state.winner,
        "agentProvider": "mock" if config.use_mock else config.openai_model,
    }
    if mode == "god":
        out["privateReasoning"] = state.private_reasoning
    if mode == "player":
        out["you"] = _you(state)
        out["awaiting"] = state.awaiting
    return out
