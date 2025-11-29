from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

@dataclass
class InventoryItem:
    id: str
    user_id: str
    item_id: str
    name: str
    durability: int
    max_durability: int
    equipped: bool
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat() + "Z"

@dataclass
class InventoryResponse:
    user_id: str
    items: List[Dict[str, Any]]

@dataclass
class AddItemRequest:
    item_id: str
    name: str
    durability: int

@dataclass
class UpdateItemRequest:
    item_id: str
    durability: Optional[int] = None
    equipped: Optional[bool] = None

@dataclass
class AddItemResponse:
    message: str
    inventory_id: str

@dataclass
class UpdateItemResponse:
    item_id: str
    durability: int
    equipped: bool
    status: str

@dataclass
class RemoveItemResponse:
    message: str
    removed_item_id: str