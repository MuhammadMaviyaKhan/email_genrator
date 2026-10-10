from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from typing import Dict, Set, Optional
import json
import asyncio

from app.db.database import get_db
from app.models.models import EmailAddress, Email, Session
from app.schemas.schemas import EmailWSMessage, WebSocketEvent
from app.services.email_service import EmailService


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_emails: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, email_id: str):
        await websocket.accept()
        
        if email_id not in self.active_connections:
            self.active_connections[email_id] = set()
        
        self.active_connections[email_id].add(websocket)
        self.connection_emails[websocket] = email_id
    
    def disconnect(self, websocket: WebSocket):
        email_id = self.connection_emails.get(websocket)
        if email_id and email_id in self.active_connections:
            self.active_connections[email_id].discard(websocket)
            if not self.active_connections[email_id]:
                del self.active_connections[email_id]
        
        self.connection_emails.pop(websocket, None)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception:
            pass
    
    async def broadcast_to_email(self, email_id: str, message: dict):
        if email_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[email_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.disconnect(conn)
    
    async def broadcast(self, message: dict):
        for email_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()
email_service = EmailService()


@router.websocket("/{email_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    email_id: str,
    token: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if token:
        result = await db.execute(
            select(Session).where(Session.token == token, Session.is_active == True)
        )
        session = result.scalar_one_or_none()
        
        if not session or session.email_address_id != email_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        if session.expires_at < datetime.utcnow():
            await websocket.close(code=4002, reason="Token expired")
            return
    else:
        result = await db.execute(
            select(EmailAddress).where(EmailAddress.id == email_id)
        )
        email_address = result.scalar_one_or_none()
        
        if not email_address or email_address.status != "active":
            await websocket.close(code=4003, reason="Email not active")
            return
    
    await manager.connect(websocket, email_id)
    
    try:
        await manager.send_personal_message(
            {
                "type": "connected",
                "email_id": email_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket
        )
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                        websocket
                    )
                
                elif message.get("type") == "subscribe":
                    pass
                
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


async def notify_new_email(email_id: str, email: Email):
    message = {
        "type": "new_email",
        "email_id": email_id,
        "data": {
            "id": str(email.id),
            "subject": email.subject,
            "from_address": email.from_address,
            "from_name": email.from_name,
            "received_at": email.received_at.isoformat() if email.received_at else None,
            "has_attachments": bool(email.attachments),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await manager.broadcast_to_email(email_id, message)


async def notify_email_status_change(email_id: str, email: Email, old_status: str, new_status: str):
    message = {
        "type": "email_status_changed",
        "email_id": email_id,
        "data": {
            "id": str(email.id),
            "old_status": old_status,
            "new_status": new_status,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await manager.broadcast_to_email(email_id, message)


async def notify_email_deleted(email_id: str, email_message_id: str):
    message = {
        "type": "email_deleted",
        "email_id": email_id,
        "data": {
            "id": email_message_id,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await manager.broadcast_to_email(email_id, message)


async def notify_email_address_expired(email_id: str):
    message = {
        "type": "email_expired",
        "email_id": email_id,
        "data": {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await manager.broadcast_to_email(email_id, message)


async def get_active_connections_count() -> int:
    return sum(len(conns) for conns in manager.active_connections.values())


async def get_connected_emails_count() -> int:
    return len(manager.active_connections)