from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

@dataclass
class Player:
    user_id: str
    sanity: float = 100.0
    dead: bool = False
    items: List[str] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []

@dataclass
class Lobby:
    id: str
    host_user_id: str
    map_id: str
    difficulty: str
    max_players: int
    players: List[Player] = None
    status: str = "open"  # open, active, closed
    created_at: str = None
    
    def __post_init__(self):
        if self.players is None:
            self.players = [Player(user_id=self.host_user_id)]
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"

@dataclass
class CreateLobbyRequest:
    host_user_id: str
    map_id: str
    difficulty: str
    max_players: int

@dataclass
class JoinLobbyRequest:
    user_id: str

@dataclass
class LeaveLobbyRequest:
    user_id: str

@dataclass
class UpdatePlayerRequest:
    sanity: Optional[float] = None
    dead: Optional[bool] = None

@dataclass
class BringItemRequest:
    user_id: str
    inventory_id: str