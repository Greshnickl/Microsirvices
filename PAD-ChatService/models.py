from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

@dataclass
class ChatMessage:
    id: str
    lobby_id: str
    sender_id: str
    sender_name: str
    message: str
    timestamp: str

@dataclass
class SendMessageRequest:
    sender_id: str
    sender_name: str
    message: str

@dataclass
class SendMessageResponse:
    status: str
    lobby_id: str
    timestamp: str

@dataclass
class ChatHistoryResponse:
    lobby_id: str
    messages: List[Dict[str, Any]]

@dataclass
class ClearChatResponse:
    message: str

@dataclass
class WebSocketMessage:
    event: str
    data: Dict[str, Any]