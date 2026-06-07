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

# Cast of 12 characters — 7 are drawn at random each game. Roles are shuffled
# every game; personalities stay per-name.
NAMES = [
    "Ronan Voss", "Seraphina Vale", "Dante Mercer", "Evelyn Ashford",
    "Lucien Crowe", "Celeste Quinn", "Kael Thorn", "Aria Blackwood",
    "Silas Drake", "Isolde Frost", "Orion Hale", "Nyx Ravenshade",
]
PERSONA = {
    "Ronan Voss":
        "a dominant ex-military leader. You speak with certainty, hate indecision, "
        "and pressure others into taking sides. Frequently wrong but rarely in doubt.",
    "Seraphina Vale":
        "calm, highly intelligent, and quietly manipulative. You rarely accuse "
        "directly — you plant ideas and let others fight over them.",
    "Dante Mercer":
        "short-tempered and confrontational. You take disagreement personally; your "
        "emotional reactions often make you look guilty even when innocent.",
    "Evelyn Ashford":
        "socially charming and diplomatic. You try to keep the peace and soften "
        "conflict — sometimes accidentally protecting wolves because you dislike harsh accusations.",
    "Lucien Crowe":
        "a paranoid strategist. You see hidden motives everywhere and build elaborate "
        "theories that are sometimes brilliant and sometimes completely absurd.",
    "Celeste Quinn":
        "coldly analytical. You focus on logic, contradictions, and voting patterns, "
        "and you distrust emotional arguments.",
    "Kael Thorn":
        "a natural liar and storyteller. Even when innocent you enjoy misleading "
        "people just to see their reactions.",
    "Aria Blackwood":
        "empathetic and observant. You read emotions more than facts and notice "
        "social dynamics others miss.",
    "Silas Drake":
        "cold, skeptical, and sarcastic. You challenge nearly every claim and make "
        "enemies regardless of alignment.",
    "Isolde Frost":
        "patient and calculating. You speak little, but every statement is deliberate — "
        "others grow suspicious simply because you reveal so little.",
    "Orion Hale":
        "a charismatic opportunist. You tend to agree with whoever currently has "
        "influence — excellent at surviving, but you rarely drive the discussion.",
    "Nyx Ravenshade":
        "an agent of chaos. You enjoy provoking conflict and throw unexpected "
        "accusations just to test reactions, helping either team.",
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
    # House-sponsored betting: users bet gas-free with just an address; the
    # operator stakes on-chain for them and pays winners out directly.
    sponsored_bets: list[dict] = field(default_factory=list)   # {marketId, address, option, amount}
    payouts: list[dict] = field(default_factory=list)          # {marketId, address, amount, txHash}

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
    """7 players: 2 wolves, 1 seer, 4 villagers — a random 7 of the 12-character
    cast each game, roles shuffled across them."""
    roles = [ROLE_WOLF, ROLE_WOLF, ROLE_SEER,
             ROLE_VILLAGER, ROLE_VILLAGER, ROLE_VILLAGER, ROLE_VILLAGER]
    random.shuffle(roles)
    cast = random.sample(NAMES, len(roles))
    players = [Player(idx=i, name=cast[i], role=roles[i]) for i in range(len(roles))]
    return GameState(players=players, max_rounds=max_rounds, pot=pot)
