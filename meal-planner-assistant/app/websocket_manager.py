from __future__ import annotations

import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    def connect(self, user_id: str, websocket: WebSocket) -> None:
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)

    async def send(self, user_id: str, data: dict) -> None:
        conns = self._connections.get(user_id, [])
        stale = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(user_id, ws)

    async def broadcast(self, data: dict) -> None:
        for user_id in list(self._connections.keys()):
            await self.send(user_id, data)


manager = ConnectionManager()
