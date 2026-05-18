from fastapi import APIRouter, Depends
from pydantic import BaseModel
from agents.dev_senior.agent import agent
from memory.dev_senior.retriever import retrieve_context
from api.auth import require_api_key
from api.sessions import new_session, get_history, set_history, delete_session

router = APIRouter(prefix="/dev-senior", tags=["Dev Senior"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    response: str
    session_id: str


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
async def chat(req: ChatRequest) -> ChatResponse:
    """Envoie un message à l'agent Dev Senior et retourne sa réponse."""
    session_id = req.session_id or new_session()
    history = get_history(session_id)

    context = retrieve_context(req.message)
    prompt = f"{context}\n\n{req.message}" if context else req.message

    result = await agent.run(prompt, message_history=history)
    set_history(session_id, result.all_messages())

    return ChatResponse(response=result.data, session_id=session_id)


@router.post("/reset/{session_id}", dependencies=[Depends(require_api_key)])
async def reset_session(session_id: str) -> dict:
    """Réinitialise l'historique d'une session."""
    delete_session(session_id)
    return {"status": "ok", "session_id": session_id}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "agent": "dev-senior"}
