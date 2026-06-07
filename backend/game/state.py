"""Core data model for a Werewolf game.

Pure data — no LLM, no chain, no I/O. The loop mutates a single GameState
instance in place; the FastAPI layer serializes it (with fog of war).
"""
from dataclasses import dataclass, field


@dataclass
class Player:
    idx: int
    name: str
    role: str                       # "wolf" | "seer" | "villager"
    alive: bool = True
    revealed_role: str | None = None
    current_speech: str | None = None


@dataclass
class Market:
    market_id: int
    type: str                       # "game_winner" | "who_voted_out"
    options: list[str]
    round: int = 1
    pools: dict[str, str] = field(default_factory=dict)
    frozen: bool = False
    resolved: bool = False
    winning_option: str | None = None


@dataclass
class GameState:
    game_id: int = 1
    phase: str = "setup"            # setup|night|morning|discussion|voting|resolution|ended
    round: int = 1
    max_rounds: int = 2
    pot: str = "1.0"
    speaking_idx: int | None = None
    players: list[Player] = field(default_factory=list)
    night_result: dict | None = None
    discussion_log: list[dict] = field(default_factory=list)
    private_reasoning: list[dict] = field(default_factory=list)
    votes: list[dict] = field(default_factory=list)
    betting_open: bool = True
    markets: list[Market] = field(default_factory=list)
    winner: str | None = None

    # transient per-round scratch (never serialized to clients)
    seer_knowledge: dict | None = None
    pending_kill: "Player | None" = None

    def alive_players(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def wolves(self) -> list[Player]:
        return [p for p in self.players if p.role == "wolf"]

    def alive_wolves(self) -> list[Player]:
        return [p for p in self.players if p.role == "wolf" and p.alive]

    def by_name(self, name: str) -> Player | None:
        if not name:
            return None
        return next((p for p in self.players if p.name.lower() == name.lower()), None)
