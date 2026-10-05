import logging
import logging.config
import uuid

import sentry_sdk
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.routes import api_router
from app.core.config import settings

# ── Structured JSON Logging ──────────────────────────────────────────────────
LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "plain": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if settings.environment == "production" else "plain",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# ── Sentry (no-op when DSN is blank) ────────────────────────────────────────
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.2,
        send_default_pii=False,
    )
    logger.info("Sentry initialized (environment=%s)", settings.environment)

# ── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="HoldIt API",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ─────────────────────────────────────────────────────────────────────
_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security Headers Middleware ───────────────────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response

# ── Request ID Middleware ─────────────────────────────────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ── Request Logging Middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "Request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "request_id": request_id,
        },
    )
    response = await call_next(request)
    logger.info(
        "Response",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "request_id": request_id,
        },
    )
    return response

# ── Lifecycle Events ──────────────────────────────────────────────────────────
import asyncio
from app.core.database import AsyncSessionLocal
from app.services.reservation_service import sweep_expired_reservations

async def sweeper_task():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                count = await sweep_expired_reservations(db)
                if count > 0:
                    logger.info(f"Swept {count} expired reservations.")
        except Exception as e:
            logger.error(f"Error in sweeper task: {e}")
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    logger.info(
        "HoldIt API starting (environment=%s, pool_size=%d)",
        settings.environment,
        settings.database_pool_size,
    )
    # Start the sweeper task in the background
    asyncio.create_task(sweeper_task())


@app.on_event("shutdown")
async def shutdown_event():
    from app.core.database import dispose_engine


    logger.info("Shutting down — closing DB connections")
    await dispose_engine()
    logger.info("Shutdown complete")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router)


# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = ["." .join(str(item) for item in error["loc"][1:]) for error in exc.errors()]
    message = ", ".join(filter(None, errors)) or "Validation error"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"success": False, "data": None, "message": message},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "data": None, "message": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "data": None, "message": "Internal server error"},
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
