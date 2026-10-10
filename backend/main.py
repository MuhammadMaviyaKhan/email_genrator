import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings
from app.core.logging.logging import setup_logging, get_logger
from app.db.database import init_db, close_db, get_db
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import router as health_router
from app.tasks.cleanup import start_background_tasks, stop_background_tasks
from app.core.exceptions import AppException
from app.core.security.security import generate_csp_nonce


setup_logging()
logger = get_logger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting TempMail Pro backend...")
    await init_db()
    await start_background_tasks()
    logger.info("Backend startup complete")
    
    yield
    
    logger.info("Shutting down TempMail Pro backend...")
    await stop_background_tasks()
    await close_db()
    logger.info("Backend shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready Temporary Email Service",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["tempmail.pro", "*.tempmail.pro", "localhost", "127.0.0.1"],
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Process-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        nonce = generate_csp_nonce()
        request.state.csp_nonce = nonce
        
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if settings.ENVIRONMENT == "production":
            csp = (
                f"default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}'; "
                f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline'; "
                f"img-src 'self' data: https:; "
                f"font-src 'self' data:; "
                f"connect-src 'self' ws: wss:; "
                f"frame-ancestors 'none'; "
                f"base-uri 'self'; "
                f"form-action 'self'"
            )
            response.headers["Content-Security-Policy"] = csp
        
        response.headers["Server"] = "TempMailPro/1.0"
        
        return response


app.add_middleware(SecurityHeadersMiddleware)


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


app.add_middleware(ProcessTimeMiddleware)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(
        f"AppException: {exc.message}",
        extra={"code": exc.code, "status_code": exc.status_code, "path": request.url.path},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "code": exc.code,
            "details": exc.details,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail} - {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TempMail Pro API</title>
        <style>
            body { font-family: system-ui, sans-serif; background: #0a0e27; color: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .container { text-align: center; }
            h1 { color: #3b82f6; }
            a { color: #60a5fa; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TempMail Pro API</h1>
            <p>Production-ready Temporary Email Service</p>
            <p><a href="/docs">API Documentation</a> | <a href="/health">Health Check</a></p>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,
        access_log=True,
    )