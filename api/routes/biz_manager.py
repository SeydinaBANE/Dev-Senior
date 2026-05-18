from fastapi import APIRouter, Depends
from pydantic import BaseModel
from agents.biz_manager.agent import agent
from memory.biz_manager.context import retrieve_context, save_interaction
from api.auth import require_api_key
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
async def chat(req: ChatRequest) -> ChatResponse:
    """Envoie un message à l'agent Business Manager et retourne sa réponse."""
    session_id = req.session_id or new_session()
    history = get_history(session_id)

    memory_context = retrieve_context(req.message)
    prompt = f"{memory_context}\n\n{req.message}" if memory_context else req.message

    result = await agent.run(prompt, message_history=history)
    response = result.data

    set_history(session_id, result.all_messages())
    save_interaction(req.message, response)

    return ChatResponse(response=response, session_id=session_id)


@router.post("/task", response_model=TaskResponse, dependencies=[Depends(require_api_key)])
async def run_task(req: TaskRequest) -> TaskResponse:
    """
    Exécution one-shot pour les workflows n8n (sans historique de session).
    Idéal pour : génération de contenu, analyse, rédaction automatisée.
    """
    prompt = f"{req.context}\n\n{req.task}" if req.context else req.task
    result = await agent.run(prompt)
    save_interaction(req.task, result.data)
    return TaskResponse(result=result.data)


@router.post("/reset/{session_id}", dependencies=[Depends(require_api_key)])
async def reset_session(session_id: str) -> dict:
    delete_session(session_id)
    return {"status": "ok", "session_id": session_id}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "agent": "biz-manager"}
