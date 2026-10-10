from fastapi import WebSocket
from typing import Dict, Set, List, Optional
import json
import asyncio
from datetime import datetime
import logging

from app.core.logging.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, dict] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, email_id: str, metadata: dict = None):
        await websocket.accept()
        async with self._lock:
            if email_id not in self.active_connections:
                self.active_connections[email_id] = set()
            self.active_connections[email_id].add(websocket)
            self.connection_metadata[websocket] = {
                "email_id": email_id,
                "connected_at": datetime.utcnow().isoformat(),
                **(metadata or {}),
            }
        logger.info(f"WebSocket connected for email {email_id}")
    
    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            metadata = self.connection_metadata.pop(websocket, None)
            if metadata:
                email_id = metadata.get("email_id")
                if email_id in self.active_connections:
                    self.active_connections[email_id].discard(websocket)
                    if not self.active_connections[email_id]:
                        del self.active_connections[email_id]
        logger.info(f"WebSocket disconnected")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            if websocket.client_state.CONNECTED:
                await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)
    
    async def send_message_to_email(self, email_id: str, message: dict):
        if email_id in self.active_connections:
            disconnected = []
            async with self._lock:
                connections = list(self.active_connections[email_id])
            
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            for conn in disconnected:
                await self.disconnect(conn)
    
    async def broadcast(self, message: dict):
        async with self._lock:
            all_connections = [
                conn for conns in self.active_connections.values() for conn in conns
            ]
        
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception:
                await self.disconnect(connection)
    
    def get_email_connections(self, email_id: str) -> int:
        return len(self.active_connections.get(email_id, set()))
    
    def get_total_connections(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_connected_emails(self) -> List[str]:
        return list(self.active_connections.keys())


manager = ConnectionManager()