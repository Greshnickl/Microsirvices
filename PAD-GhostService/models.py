from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

@dataclass
class Ghost:
    id: str
    name: str
    type_a_symptoms: List[str] = None
    type_b_symptoms: List[str] = None
    type_c_symptoms: List[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.type_a_symptoms is None:
            self.type_a_symptoms = []
        if self.type_b_symptoms is None:
            self.type_b_symptoms = []
        if self.type_c_symptoms is None:
            self.type_c_symptoms = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat() + "Z"

@dataclass
class CreateGhostRequest:
    name: str
    type_a_symptoms: List[str] = None
    type_b_symptoms: List[str] = None
    type_c_symptoms: List[str] = None
    
    def __post_init__(self):
        if self.type_a_symptoms is None:
            self.type_a_symptoms = []
        if self.type_b_symptoms is None:
            self.type_b_symptoms = []
        if self.type_c_symptoms is None:
            self.type_c_symptoms = []

@dataclass
class UpdateGhostRequest:
    name: Optional[str] = None
    type_a_symptoms: Optional[List[str]] = None
    type_b_symptoms: Optional[List[str]] = None
    type_c_symptoms: Optional[List[str]] = None

@dataclass
class GhostsResponse:
    ghosts: List[Dict[str, Any]]