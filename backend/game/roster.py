"""new_game() to start a fresh match. Cast pool lives in characters.py."""
import random

from .characters import NAMES
from .state import GameState, Player

ROLES = ["wolf", "wolf", "seer", "villager", "villager", "villager", "villager"]


def new_game(game_id: int = 1) -> GameState:
    """7 players (2 wolves, 1 seer, 4 villagers), drawn randomly from the pool."""
    cast = random.sample(NAMES, len(ROLES))  # pick 7 of the 12 characters
    roles = ROLES[:]
    random.shuffle(roles)
    players = [Player(idx=i, name=cast[i], role=roles[i]) for i in range(len(ROLES))]
    return GameState(game_id=game_id, players=players)
