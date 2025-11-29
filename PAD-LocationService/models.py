from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

@dataclass
class LocationSample:
    user_id: str
    lobby_id: str
    room_id: str
    is_speaking: bool
    group: List[str]
    is_hiding: bool
    at: str

@dataclass
class TrackLocationRequest:
    user_id: str
    lobby_id: str
    room_id: str
    is_speaking: bool
    group: List[str]
    is_hiding: bool
    at: str
    
    def __post_init__(self):
        if self.group is None:
            self.group = []

@dataclass
class LatestLocationResponse:
    room_id: str
    is_alone: bool
    last_seen_at: str

@dataclass
class LocationHistory:
    user_id: str
    lobby_id: str
    room_id: str
    is_speaking: bool
    group: List[str]
    is_hiding: bool
    recorded_at: str
    created_at: str