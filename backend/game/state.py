"""Game state model + 7-player roster. Serialization to the 02-INTERFACES JSON
shape lives in server.py (so fog-of-war is enforced there)."""
from __future__ import annotations

from dataclasses import dataclass, field
import random

# Roles + the contract's Role enum (1=Wolf, 2=Villager, 3=Seer).
ROLE_WOLF = "wolf"
ROLE_SEER = "seer"
ROLE_VILLAGER = "villager"
ROLE_TO_ENUM = {ROLE_WOLF: 1, ROLE_VILLAGER: 2, ROLE_SEER: 3}

TEAM_WOLVES = "wolves"
TEAM_VILLAGE = "village"

# 7 fixed characters. Roles are shuffled each game; personalities stay per-name.
NAMES = ["Luna", "Caspian", "Mira", "Theron", "Dax", "Vera", "Orin"]
PERSONA = {
    "Luna": "measured and analytical; you cite specific things people said.",
    "Caspian": "charming; you deflect with light humour and rarely accuse directly.",
    "Mira": "blunt and aggressive; you make bold accusations.",
    "Theron": "quiet; you speak late and sound conclusive when you do.",
    "Dax": "anxious and suspicious of almost everyone.",
    "Vera": "a calm mediator who weighs both sides before judging.",
    "Orin": "coldly logical; you talk in probabilities and tells.",
}


@dataclass
class Player:
    idx: int
    name: str
    role: str                       # "wolf" | "seer" | "villager"
    alive: bool = True
    revealed_role: str | None = None
    current_speech: str | None = None        # the line to show in the speech bubble, or None
    salt: str = "0x" + "11" * 32             # per-player salt for the role-hash commitment

    @property
    def avatar_seed(self) -> str:
        return self.name


@dataclass
class Market:
    market_id: int
    type: str                       # "game_winner" | "who_voted_out"
    options: list[str]
    round: int = 1
    pools: dict[str, str] = field(default_factory=dict)   # option -> MON staked (string)
    frozen: bool = False
    resolved: bool = False
    winning_option: str | None = None

    def to_json(self) -> dict:
        return {
            "marketId": self.market_id,
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
    winner: str | None = None       # "wolves" | "village"
    seer_known: dict[str, str] = field(default_factory=dict)   # name -> role, accumulates each night

    # --- helpers -----------------------------------------------------------
    def alive_players(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def wolves(self) -> list[Player]:
        return [p for p in self.players if p.role == ROLE_WOLF]

    def alive_wolves(self) -> list[Player]:
        return [p for p in self.alive_players() if p.role == ROLE_WOLF]

    def alive_village(self) -> list[Player]:
        return [p for p in self.alive_players() if p.role != ROLE_WOLF]

    def by_name(self, name: str | None) -> Player | None:
        if not name:
            return None
        return next((p for p in self.players if p.name.lower() == name.lower()), None)


def new_game(max_rounds: int = 2, pot: str = "1.0") -> GameState:
    """7 players: 2 wolves, 1 seer, 4 villagers — roles shuffled across the names."""
    roles = [ROLE_WOLF, ROLE_WOLF, ROLE_SEER,
             ROLE_VILLAGER, ROLE_VILLAGER, ROLE_VILLAGER, ROLE_VILLAGER]
    random.shuffle(roles)
    players = [Player(idx=i, name=NAMES[i], role=roles[i]) for i in range(len(NAMES))]
    return GameState(players=players, max_rounds=max_rounds, pot=pot)
