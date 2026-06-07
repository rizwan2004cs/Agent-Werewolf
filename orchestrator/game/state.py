"""Game state model + serialization to the INTERFACES.md JSON shape."""
from __future__ import annotations

from dataclasses import dataclass, field


# Role / team constants shared with the contract (Role enum: 1=Wolf,2=Villager,3=Seer)
ROLE_WOLF = "wolf"
ROLE_VILLAGER = "villager"
ROLE_SEER = "seer"

ROLE_TO_ENUM = {ROLE_WOLF: 1, ROLE_VILLAGER: 2, ROLE_SEER: 3}
TEAM_WOLF = "wolves"
TEAM_VILLAGE = "village"


@dataclass
class Player:
    idx: int
    name: str
    address: str
    role: str                      # "wolf" | "villager" | "seer"
    alive: bool = True
    revealed_role: str | None = None
    last_speech: str | None = None
    salt: str = "0x" + "00" * 32   # per-player salt for the role commitment


@dataclass
class Market:
    market_id: int
    game_id: int
    type: str                      # who_voted_out | catches_wolf_this_round | game_winner | seer_survives
    round: int
    options: list[str]
    pools: dict[str, str] = field(default_factory=dict)   # option -> MON staked (string)
    frozen: bool = False
    resolved: bool = False
    winning_option: str | None = None

    def to_json(self) -> dict:
        return {
            "marketId": self.market_id,
            "gameId": self.game_id,
            "type": self.type,
            "round": self.round,
            "options": self.options,
            "pools": {opt: self.pools.get(opt, "0.0") for opt in self.options},
            "frozen": self.frozen,
            "resolved": self.resolved,
            "winningOption": self.winning_option,
        }


@dataclass
class GameState:
    game_id: int = 0
    phase: str = "setup"           # setup|night|morning|discussion|voting|resolution|ended
    round: int = 1
    max_rounds: int = 2
    pot: str = "0"
    players: list[Player] = field(default_factory=list)
    discussion_log: list[dict] = field(default_factory=list)
    private_reasoning: list[dict] = field(default_factory=list)
    night_result: dict | None = None
    votes: list[dict] = field(default_factory=list)
    betting_open: bool = True
    markets: list[Market] = field(default_factory=list)
    winner: str | None = None      # "wolves" | "village"

    # --- helpers -----------------------------------------------------------
    def alive_players(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def by_name(self, name: str) -> Player | None:
        return next((p for p in self.players if p.name.lower() == name.lower()), None)

    def alive_wolves(self) -> list[Player]:
        return [p for p in self.alive_players() if p.role == ROLE_WOLF]

    def alive_village(self) -> list[Player]:
        return [p for p in self.alive_players() if p.role != ROLE_WOLF]


def serialize(state: GameState) -> dict:
    """Full (god-mode) serialization. Fog-of-war stripping happens in server.py."""
    return {
        "gameId": state.game_id,
        "phase": state.phase,
        "round": state.round,
        "maxRounds": state.max_rounds,
        "pot": state.pot,
        "players": [
            {
                "idx": p.idx,
                "name": p.name,
                "address": p.address,
                "alive": p.alive,
                "role": p.role,                 # stripped for bettor mode in server.py
                "revealedRole": p.revealed_role,
                "lastSpeech": p.last_speech,
            }
            for p in state.players
        ],
        "nightResult": state.night_result,
        "discussionLog": state.discussion_log,
        "privateReasoning": state.private_reasoning,  # omitted for bettor mode
        "votes": state.votes,
        "bettingOpen": state.betting_open,
        "markets": [m.to_json() for m in state.markets],
        "winner": state.winner,
    }
