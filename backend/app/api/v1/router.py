from fastapi import APIRouter

from app.api.v1.endpoints import emails, addresses, auth, websocket, health, admin


api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["Email Addresses"])
api_router.include_router(emails.router, prefix="/emails", tags=["Emails"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])