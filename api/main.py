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
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from observability.langfuse_config import configure_observability, flush as langfuse_flush
from agents.dev_senior.agent import agent as dev_agent
from agents.biz_manager.agent import agent as biz_agent
from api.db import create_pool
from api.routes.dev_senior import router as dev_router
from api.routes.biz_manager import router as biz_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_observability("agents-api")
    app.state.pool = await create_pool()
    async with dev_agent.run_mcp_servers():
        async with biz_agent.run_mcp_servers():
            yield
    await app.state.pool.close()
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


@app.get("/health", tags=["Infra"])
async def health() -> dict:
    """Health check public (pas d'auth requise — utilisé par healthcheck.sh)."""
    return {"status": "ok", "agents": ["dev-senior", "biz-manager"]}
