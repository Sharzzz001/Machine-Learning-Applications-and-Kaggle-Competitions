from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Player(BaseModel):
    name: str
    is_ai: bool
    resources: Dict[str, int] = {"Wood": 0, "Brick": 0, "Sheep": 0, "Wheat": 0, "Ore": 0}
    victory_points: int = 0
    dev_cards: Dict[str, int] = {
        "Unknown": 0, # For opponents
        "Knight": 0, "VP": 0, "Roads": 0, "Plenty": 0, "Monopoly": 0
    }

class HexTile(BaseModel):
    q: int
    r: int
    resource: Optional[str] = None
    number: Optional[int] = None

class GameState(BaseModel):
    players: List[Player] = []
    current_turn_index: int = 0
    board_tiles: List[HexTile] = []

    def initialize_snake_draft(self):
        # For 4 players: [0, 1, 2, 3, 3, 2, 1, 0]
        # For 3 players: [0, 1, 2, 2, 1, 0]
        indices = list(range(len(self.players)))
        self.draft_order = indices + indices[::-1]
        self.draft_turn = 0
        self.phase = "SETUP_PLACEMENTS" # New phase!

    def get_draft_player(self):
        player_index = self.draft_order[self.draft_turn]
        return self.players[player_index]
    
    def add_player(self, name: str, is_ai: bool):
        self.players.append(Player(name=name, is_ai=is_ai))

    def get_current_player(self) -> Player:
        return self.players[self.current_turn_index]

    def next_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)