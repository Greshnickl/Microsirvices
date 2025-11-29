from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

@dataclass
class Room:
    id: str
    name: str

@dataclass
class Connection:
    from_room: str
    to_room: str

@dataclass
class MapObject:
    id: str
    room_id: str
    type: str
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}

@dataclass
class HidingSpot:
    id: str
    room_id: str
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}

@dataclass
class Map:
    id: str
    name: str
    rooms: List[Room] = None
    connections: List[Connection] = None
    objects: List[MapObject] = None
    hiding_spots: List[HidingSpot] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.rooms is None:
            self.rooms = []
        if self.connections is None:
            self.connections = []
        if self.objects is None:
            self.objects = []
        if self.hiding_spots is None:
            self.hiding_spots = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat() + "Z"

@dataclass
class CreateMapRequest:
    name: str
    rooms: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.rooms is None:
            self.rooms = []

@dataclass
class UpdateMapRequest:
    name: Optional[str] = None

@dataclass
class MapsResponse:
    total: int
    page: int
    page_size: int
    maps: List[Dict[str, Any]]