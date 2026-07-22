"""FastAPI application entrypoint for the Auth & RBAC module.

Run locally with::

    cd backend
    uvicorn app.main:app --reload

Only Authentication & RBAC are wired here. Graph Intelligence and Financial
Crime routers are intentionally out of scope for this step; their protected
placeholders live in ``app/routers/protected.py``.
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppHTTPException
from app.core.logging import get_logger
from app.financial.routers import financial as financial_router
from app.graph.routers import graph as graph_router
from app.chat.router import router as chat_router
from app.routers import admin, analytics, auth, network, predict, protected

logger = get_logger("api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Authentication & Role-Based Access Control module.",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    # Allow any Render / Vercel deployment subdomain regardless of the
    # BACKEND_CORS_ORIGINS env var, so the deployed frontend can call the API
    # directly from the browser (e.g. the /network page's direct fetch).
    allow_origin_regex=r"https://.*\.(onrender\.com|vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers → consistent error envelope ────────────────────────
@app.exception_handler(AppHTTPException)
async def app_http_exception_handler(request: Request, exc: AppHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "request validation failed",
                "details": exc.errors(),
            }
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(protected.router, prefix=settings.API_V1_PREFIX)
app.include_router(graph_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)
app.include_router(financial_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(network.router, prefix=settings.API_V1_PREFIX)
app.include_router(predict.router, prefix=settings.API_V1_PREFIX)


# ── Lifecycle ─────────────────────────────────────────────────────────────
@app.on_event("startup")
def _startup_init() -> None:
    """Initialize DB tables & baseline seed asynchronously in background thread.

    This ensures uvicorn binds to port 9000 immediately, satisfying Catalyst's
    liveness health check without blocking on DB connection latency.
    """
    import threading

    def _bg_init():
        try:
            from app.core.database import engine, Base
            import app.models.rbac  # noqa: F401
            logger.info("Creating database tables if they do not exist...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables ready.")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")

        try:
            from app.seed import seed
            logger.info("Running automatic DB seeding...")
            seed()
            logger.info("Automatic DB seeding completed.")
        except Exception as e:
            logger.error(f"Failed to auto-seed database: {e}")

        try:
            import os
            from app.core.config import settings
            duckdb_path = settings.DUCKDB_PATH
            datasets_dir = settings.resolved_datasets_dir
            if not os.path.exists(duckdb_path):
                logger.info("DuckDB file missing, building from datasets + generating synthetic cases...")
                from app.chat.data.case_generator import generate
                from pathlib import Path
                synth_dir = os.path.join(datasets_dir, "synthetic_cases")
                generate(out_dir=Path(synth_dir))
                from app.chat.data.loader import build_database
                build_database(datasets_dir=datasets_dir, duckdb_path=duckdb_path)
                logger.info("DuckDB database built successfully.")
            else:
                logger.info("DuckDB file found at %s, skipping build.", duckdb_path)
        except Exception as e:
            logger.error(f"Failed to build DuckDB database on startup: {e}")

    threading.Thread(target=_bg_init, daemon=True).start()


@app.on_event("shutdown")
def _shutdown_graph() -> None:
    """Close the shared Neo4j driver cleanly on application shutdown."""
    from app.graph.connection import graph_connection

    graph_connection.close()


@app.get("/health", tags=["system"], summary="Liveness probe")
def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/health/graph", tags=["system"], summary="Graph DB connectivity probe")
def health_graph():
    from app.graph.connection import graph_connection

    ok = graph_connection.verify_connectivity()
    return {"status": "ok" if ok else "unavailable", "component": "neo4j"}


@app.get("/", tags=["system"], include_in_schema=False)
def root():
    return {"service": settings.PROJECT_NAME, "docs": "/docs"}
