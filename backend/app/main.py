from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import logging

from app.core.config import settings
from app.db.database import init_db, close_db, get_db
from app.api.v1.router import api_router
from app.api.v1.dependencies import RateLimiter
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.services.smtp_receiver import receiver as smtp_receiver
from app.tasks.cleanup import start_background_tasks, stop_background_tasks


setup_logging()
logger = logging.getLogger(__name__)

rate_limiter = RateLimiter()


async def _seed_default_domains():
    from sqlalchemy import select
    from app.db.database import async_session_maker
    from app.models.models import Domain
    from app.core.config import settings

    async with async_session_maker() as db:
        for idx, domain in enumerate(settings.DEFAULT_DOMAINS):
            result = await db.execute(select(Domain).where(Domain.domain == domain))
            if result.scalar_one_or_none() is None:
                db.add(
                    Domain(
                        domain=domain,
                        is_active=True,
                        is_default=(idx == 0),
                    )
                )
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up TempMail Pro...")
    await init_db()
    logger.info("Database initialized")
    await _seed_default_domains()
    logger.info("Default domains seeded")
    try:
        await start_background_tasks()
        smtp_receiver.start()
    except Exception as e:
        logger.error(f"Failed to start background services: {e}")
    yield
    logger.info("Shutting down TempMail Pro...")
    smtp_receiver.stop()
    await stop_background_tasks()
    await close_db()
    logger.info("Database connections closed")


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
        allowed_hosts=["tempmail.pro", "*.tempmail.pro", "localhost"],
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if settings.RATE_LIMIT_ENABLED:
        client_ip = request.client.host if request.client else "unknown"
        allowed, retry_after = await rate_limiter.check_rate_limit(
            identifier=client_ip,
            endpoint=str(request.url.path),
            limit=settings.RATE_LIMIT_REQUESTS,
            window=settings.RATE_LIMIT_WINDOW_SECONDS,
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"AppException: {exc.message}", extra={"code": exc.code, "details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code, "details": exc.details},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check(db=Depends(get_db)):
    try:
        await db.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "database": "disconnected"},
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )