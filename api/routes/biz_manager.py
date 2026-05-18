import asyncpg
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessagesTypeAdapter

from agents.biz_manager.agent import agent
from memory.biz_manager.context import retrieve_context, save_interaction
from observability.langfuse_config import get_langfuse
from api.auth import require_api_key
from api.db import get_pool
from api.sessions import new_session, get_history, set_history, delete_session

router = APIRouter(prefix="/biz-manager", tags=["Business Manager"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    response: str
    session_id: str


class TaskRequest(BaseModel):
    """Pour les appels directs depuis n8n sans session (one-shot)."""
    task: str
    context: str = ""


class TaskResponse(BaseModel):
    result: str


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    """Envoie un message à l'agent Business Manager et retourne sa réponse."""
    pool: asyncpg.Pool = get_pool(request)
    session_id = req.session_id or await new_session(pool, "biz-manager")
    history_raw = await get_history(pool, session_id)
    history = ModelMessagesTypeAdapter.validate_python(history_raw) if history_raw else []

    memory_context = retrieve_context(req.message)
    prompt = f"{memory_context}\n\n{req.message}" if memory_context else req.message

    lf = get_langfuse()
    trace = lf.trace(
        name="biz-manager-chat",
        session_id=session_id,
        input={"message": req.message},
        metadata={"agent": "biz-manager"},
    ) if lf else None

    result = await agent.run(prompt, message_history=history)
    response = result.data

    if trace:
        try:
            trace.update(output={"response": response})
        except Exception:
            pass

    messages = ModelMessagesTypeAdapter.dump_python(result.all_messages(), mode="json")
    await set_history(pool, session_id, messages)
    save_interaction(req.message, response)

    return ChatResponse(response=response, session_id=session_id)


@router.post("/task", response_model=TaskResponse, dependencies=[Depends(require_api_key)])
async def run_task(req: TaskRequest) -> TaskResponse:
    """Exécution one-shot pour les workflows n8n (sans historique de session)."""
    lf = get_langfuse()
    trace = lf.trace(
        name="biz-manager-task",
        input={"task": req.task},
        metadata={"agent": "biz-manager", "type": "one-shot"},
    ) if lf else None

    prompt = f"{req.context}\n\n{req.task}" if req.context else req.task
    result = await agent.run(prompt)
    response = result.data

    if trace:
        try:
            trace.update(output={"result": response})
        except Exception:
            pass

    save_interaction(req.task, response)
    return TaskResponse(result=response)


@router.post("/reset/{session_id}", dependencies=[Depends(require_api_key)])
async def reset_session(session_id: str, request: Request) -> dict:
    pool: asyncpg.Pool = get_pool(request)
    await delete_session(pool, session_id)
    return {"status": "ok", "session_id": session_id}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "agent": "biz-manager"}
