"""
API HTTP — expose les deux agents pour les workflows n8n.

Démarrage :
    make api                    # port 8080 par défaut
    make api PORT=9000          # port custom

Endpoints :
    POST /dev-senior/chat       → agent Dev Senior (avec session)
    POST /biz-manager/chat      → agent Business Manager (avec session)
    POST /biz-manager/task      → one-shot sans session (pour n8n)
    GET  /health                → statut global
    GET  /docs                  → Swagger UI (auto-généré)
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import logfire
from fastapi import FastAPI

from observability.logfire_config import configure_logfire
from agents.dev_senior.agent import agent as dev_agent
from agents.biz_manager.agent import agent as biz_agent
from api.routes.dev_senior import router as dev_router
from api.routes.biz_manager import router as biz_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lance les MCP servers une fois au démarrage, les arrête proprement."""
    configure_logfire("agents-api")
    async with dev_agent.run_mcp_servers():
        async with biz_agent.run_mcp_servers():
            yield


app = FastAPI(
    title="Agents IA — API interne",
    description="API REST pour les agents Dev Senior et Business Manager",
    version="0.1.0",
    lifespan=lifespan,
)

logfire.instrument_fastapi(app)

app.include_router(dev_router)
app.include_router(biz_router)


@app.get("/health", tags=["Infra"])
async def health() -> dict:
    return {"status": "ok", "agents": ["dev-senior", "biz-manager"]}
