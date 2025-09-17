from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        # The websocket must already be accepted by the router endpoint.
        self.active_connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        conns = self.active_connections.get(user_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: dict):
        conns = self.active_connections.get(user_id, set())
        to_remove: Set[WebSocket] = set()
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                to_remove.add(ws)
        for ws in to_remove:
            self.disconnect(user_id, ws)


manager = ConnectionManager()
