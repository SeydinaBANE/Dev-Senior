import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessagesTypeAdapter

from agents.biz_manager.agent import agent
from api.auth import require_api_key
from api.file_extractor import extract_text
from api.sessions import SessionStore
from memory.biz_manager.context import retrieve_context, save_interaction
from observability.langfuse_config import get_langfuse

router = APIRouter(prefix="/biz-manager", tags=["Business Manager"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    document_context: str = ""


class ChatResponse(BaseModel):
    response: str
    session_id: str


class TaskRequest(BaseModel):
    """Pour les appels directs depuis n8n sans session (one-shot)."""

    task: str
    context: str = ""


class TaskResponse(BaseModel):
    result: str


class UploadResponse(BaseModel):
    filename: str
    text: str
    size_chars: int


def _build_prompt(message: str, memory_context: str, document_context: str) -> str:
    parts = []
    if memory_context:
        parts.append(memory_context)
    if document_context:
        parts.append(f"[Document joint]\n{document_context}")
    parts.append(message)
    return "\n\n".join(parts)


@router.post("/upload", response_model=UploadResponse, dependencies=[Depends(require_api_key)])
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """Extrait le texte d'un fichier. Le client renvoie ce texte dans document_context."""
    content = await file.read()
    try:
        text = extract_text(file.filename or "", content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return UploadResponse(filename=file.filename or "document", text=text, size_chars=len(text))


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    """Envoie un message à l'agent Business Manager et retourne sa réponse."""
    sessions: SessionStore = request.app.state.sessions
    session_id = req.session_id or await sessions.new_session("biz-manager")
    history_raw = await sessions.get_history(session_id)
    history = ModelMessagesTypeAdapter.validate_python(history_raw) if history_raw else []

    memory_context = retrieve_context(req.message)
    prompt = _build_prompt(req.message, memory_context, req.document_context)

    lf = get_langfuse()
    trace = (
        lf.trace(
            name="biz-manager-chat",
            session_id=session_id,
            input={"message": req.message},
            metadata={"agent": "biz-manager"},
        )
        if lf
        else None
    )

    result = await agent.run(prompt, message_history=history)
    response = result.data

    if trace:
        try:
            trace.update(output={"response": response})
        except Exception:
            pass

    messages = ModelMessagesTypeAdapter.dump_python(result.all_messages(), mode="json")
    await sessions.set_history(session_id, messages)
    save_interaction(req.message, response)

    return ChatResponse(response=response, session_id=session_id)


@router.post("/chat/stream", dependencies=[Depends(require_api_key)])
async def chat_stream(req: ChatRequest, request: Request) -> StreamingResponse:
    """SSE : stream token-par-token la réponse de l'agent Business Manager."""
    sessions: SessionStore = request.app.state.sessions
    session_id = req.session_id or await sessions.new_session("biz-manager")
    history_raw = await sessions.get_history(session_id)
    history = ModelMessagesTypeAdapter.validate_python(history_raw) if history_raw else []

    memory_context = retrieve_context(req.message)
    prompt = _build_prompt(req.message, memory_context, req.document_context)

    lf = get_langfuse()
    trace = (
        lf.trace(
            name="biz-manager-chat-stream",
            session_id=session_id,
            input={"message": req.message},
            metadata={"agent": "biz-manager", "streaming": True},
        )
        if lf
        else None
    )

    async def generate() -> AsyncGenerator[str, None]:
        yield f"event: session\ndata: {session_id}\n\n"
        chunks: list[str] = []
        try:
            async with agent.run_stream(prompt, message_history=history) as result:
                async for delta in result.stream_text(delta=True):
                    chunks.append(delta)
                    yield f"data: {json.dumps(delta)}\n\n"
                messages = ModelMessagesTypeAdapter.dump_python(result.all_messages(), mode="json")
                await sessions.set_history(session_id, messages)
            response_text = "".join(chunks)
            save_interaction(req.message, response_text)
            if trace:
                try:
                    trace.update(output={"response": response_text})
                except Exception:
                    pass
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps(str(exc))}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/task", response_model=TaskResponse, dependencies=[Depends(require_api_key)])
async def run_task(req: TaskRequest) -> TaskResponse:
    """Exécution one-shot pour les workflows n8n (sans historique de session)."""
    lf = get_langfuse()
    trace = (
        lf.trace(
            name="biz-manager-task",
            input={"task": req.task},
            metadata={"agent": "biz-manager", "type": "one-shot"},
        )
        if lf
        else None
    )

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
    await request.app.state.sessions.delete_session(session_id)
    return {"status": "ok", "session_id": session_id}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "agent": "biz-manager"}
