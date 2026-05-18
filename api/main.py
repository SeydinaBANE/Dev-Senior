"""
API HTTP — expose les deux agents pour les workflows n8n et le frontend React.

Démarrage :
    make api                    # port 8080 par défaut

Endpoints :
    POST /dev-senior/chat       → agent Dev Senior (avec session)
    POST /biz-manager/chat      → agent Business Manager (avec session)
    POST /biz-manager/task      → one-shot sans session (pour n8n)
    GET  /health                → statut global (sans auth)
    GET  /docs                  → Swagger UI (auto-généré)

Sécurité :
    Tous les endpoints (sauf /health) requièrent le header X-API-Key
    si AGENTS_API_KEY est défini dans .env.
"""
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from observability.langfuse_config import configure_observability, flush as langfuse_flush
from agents.dev_senior.agent import agent as dev_agent
from agents.biz_manager.agent import agent as biz_agent
from api.sessions import SessionStore
from api.routes.dev_senior import router as dev_router
from api.routes.biz_manager import router as biz_router
from api.routes.metrics import router as metrics_router
from api.metrics_store import record_request


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_observability("agents-api")
    app.state.sessions = await SessionStore.create()
    async with dev_agent.run_mcp_servers():
        async with biz_agent.run_mcp_servers():
            yield
    await app.state.sessions.close()
    langfuse_flush()


app = FastAPI(
    title="Agents IA — API interne",
    description="API REST pour les agents Dev Senior et Business Manager",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("DOCS_ENABLED", "true").lower() != "false" else None,
    redoc_url=None,
)

# CORS — inclut le frontend React (port 5173) + n8n (5678) + dev local
_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5678,http://localhost:3000,http://127.0.0.1:5678",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(dev_router)
app.include_router(biz_router)
app.include_router(metrics_router)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next) -> Response:  # type: ignore[type-arg]
    start = time.monotonic()
    response: Response = await call_next(request)
    latency_ms = (time.monotonic() - start) * 1000
    path = request.url.path
    if "/dev-senior/" in path:
        record_request("dev-senior", latency_ms, error=response.status_code >= 400)
    elif "/biz-manager/" in path:
        record_request("biz-manager", latency_ms, error=response.status_code >= 400)
    return response

# Frontend statique — monté en dernier pour ne pas masquer les routes API.
# En prod : `make serve-prod` build le frontend puis démarre l'API.
# Accessible sur http://localhost:8080/app
_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/app", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")


@app.get("/health", tags=["Infra"])
async def health() -> dict:
    """Health check public (pas d'auth requise — utilisé par healthcheck.sh)."""
    return {"status": "ok", "agents": ["dev-senior", "biz-manager"]}
