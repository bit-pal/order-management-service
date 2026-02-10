"""
Order management service. FastAPI app with CORS, rate limiting, Swagger.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.auth import router as auth_router, get_token_router
from app.api.orders import router as orders_router
from app.config import settings
from app.core.redis_client import redis_order_cache


def get_limiter():
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    return Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    )


limiter = get_limiter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure Redis client can connect. Shutdown: close Redis."""
    await redis_order_cache.connect()
    yield
    await redis_order_cache.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Order Management Service",
        description="API for orders with auth, cache, message queue and background tasks.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CORS
    app.add_middleware(
        "CORSMiddleware",
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes under API prefix
    prefix = settings.api_prefix
    app.include_router(auth_router, prefix=prefix)
    app.include_router(get_token_router(), prefix=prefix)
    app.include_router(orders_router, prefix=prefix)

    return app


app = create_app()

# Apply rate limit to all routes (global)
@app.get("/")
async def root():
    return {"service": "Order Management API", "docs": "/docs"}
