import asyncpg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessagesTypeAdapter

from agents.dev_senior.agent import agent
from memory.dev_senior.retriever import retrieve_context
from observability.langfuse_config import get_langfuse
from api.auth import require_api_key
from api.db import get_pool
from api.sessions import new_session, get_history, set_history, delete_session

router = APIRouter(prefix="/dev-senior", tags=["Dev Senior"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    response: str
    session_id: str


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    """Envoie un message à l'agent Dev Senior et retourne sa réponse."""
    pool: asyncpg.Pool = get_pool(request)
    session_id = req.session_id or await new_session(pool, "dev-senior")
    history_raw = await get_history(pool, session_id)
    history = ModelMessagesTypeAdapter.validate_python(history_raw) if history_raw else []

    context = retrieve_context(req.message)
    prompt = f"{context}\n\n{req.message}" if context else req.message

    lf = get_langfuse()
    trace = lf.trace(
        name="dev-senior-chat",
        session_id=session_id,
        input={"message": req.message},
        metadata={"agent": "dev-senior"},
    )

    result = await agent.run(prompt, message_history=history)
    response = result.data

    trace.update(output={"response": response})

    messages = ModelMessagesTypeAdapter.dump_python(result.all_messages(), mode="json")
    await set_history(pool, session_id, messages)

    return ChatResponse(response=response, session_id=session_id)


@router.post("/reset/{session_id}", dependencies=[Depends(require_api_key)])
async def reset_session(session_id: str, request: Request) -> dict:
    """Réinitialise l'historique d'une session."""
    pool: asyncpg.Pool = get_pool(request)
    await delete_session(pool, session_id)
    return {"status": "ok", "session_id": session_id}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "agent": "dev-senior"}
