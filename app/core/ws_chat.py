from typing import Dict, Set
from fastapi import WebSocket


class ChatConnectionManager:
    """Manager for chat WebSocket connections per conversation"""

    def __init__(self) -> None:
        # conversation_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, conversation_id: int, websocket: WebSocket):
        """Connect websocket to a conversation"""
        self.active_connections.setdefault(conversation_id, set()).add(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket):
        """Disconnect websocket from a conversation"""
        conns = self.active_connections.get(conversation_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active_connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: int, message: dict):
        """Broadcast message to all connections in a conversation"""
        conns = self.active_connections.get(conversation_id, set())
        to_remove: Set[WebSocket] = set()
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                to_remove.add(ws)
        for ws in to_remove:
            self.disconnect(conversation_id, ws)


chat_manager = ChatConnectionManager()
