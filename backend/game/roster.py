"""new_game() to start a fresh match. Cast lives in characters.py."""
import random

from .characters import NAMES
from .state import GameState, Player


def new_game(game_id: int = 1) -> GameState:
    """7 players drawn at random from the 12-character cast:
    2 wolves, 1 seer, 4 villagers — roles shuffled."""
    roles = ["wolf", "wolf", "seer", "villager", "villager", "villager", "villager"]
    random.shuffle(roles)
    cast = random.sample(NAMES, 7)
    players = [Player(idx=i, name=cast[i], role=roles[i]) for i in range(7)]
    return GameState(game_id=game_id, players=players)
