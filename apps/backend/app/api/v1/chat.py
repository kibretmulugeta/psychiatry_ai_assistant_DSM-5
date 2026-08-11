"""
Chat API Router supporting REST endpoint, SSE Streaming, and WebSocket connections with RAG Retrieval.
"""

import json
import uuid
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.api.deps import (
    get_action_agent,
    get_db_session,
    get_knowledge_agent,
    get_router_agent,
)
from apps.backend.app.schemas.chat import ChatRequest, ChatResponse, SourceAttributionSchema
from packages.agents.action_agent import ActionAgent
from packages.agents.knowledge_agent import KnowledgeAgent
from packages.agents.router_agent import RouterAgent
from packages.database.repositories.conversation_repo import ConversationRepository
from packages.database.repositories.message_repo import MessageRepository
from packages.llm.base import LLMMessage

router = APIRouter(prefix="/chat", tags=["Chat & Streaming"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
@router.post("/message", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_message(
    request: ChatRequest,
    router_agent: RouterAgent = Depends(get_router_agent),
    knowledge_agent: KnowledgeAgent = Depends(get_knowledge_agent),
    action_agent: ActionAgent = Depends(get_action_agent),
) -> ChatResponse:
    """Standard REST Chat Endpoint. Classifies intent and routes to Knowledge or Action Agent."""
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"
    db = None

    decision = await router_agent.process(input_text=request.message)

    action_payload = None
    response_text = ""
    tokens_used = 0
    sources_payload = []

    if decision.action_name or decision.route == "ACTION":
        action_res = await action_agent.process(
            input_text=request.message,
            action_name=decision.action_name,
            action_args=decision.action_args,
        )
        response_text = action_res.message
        action_payload = {"action_name": action_res.action_name, "data": action_res.data}
    else:
        history_msgs = [LLMMessage(role=m.role, content=m.content) for m in (request.history or [])]
        know_res = await knowledge_agent.process(
            input_text=request.message,
            history=history_msgs,
            session=db,
        )
        response_text = know_res.content
        tokens_used = know_res.tokens_used
        sources_payload = [
            SourceAttributionSchema(
                document_id=s.document_id,
                filename=s.filename,
                chunk_index=s.chunk_index,
                similarity_score=s.similarity_score,
                snippet=s.snippet,
            )
            for s in know_res.sources
        ]

    # Attempt assistant message persistence if DB is connected
    if conversation:
        try:
            await msg_repo.create(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                tokens_used=tokens_used,
            )
        except Exception:
            pass

    return ChatResponse(
        response=response_text,
        route=decision.route,
        session_id=session_id,
        action=action_payload,
        sources=sources_payload,
        tokens_used=tokens_used,
    )


@router.get("/stream")
async def chat_stream(
    message: str = Query(..., min_length=1, description="Visitor query text"),
    session_id: str = Query(default_factory=lambda: f"sess_{uuid.uuid4().hex[:12]}"),
    router_agent: RouterAgent = Depends(get_router_agent),
    knowledge_agent: KnowledgeAgent = Depends(get_knowledge_agent),
    action_agent: ActionAgent = Depends(get_action_agent),
) -> StreamingResponse:
    """SSE (Server-Sent Events) Token-by-Token Streaming Endpoint."""

    async def sse_event_generator() -> AsyncGenerator[str, None]:
        decision = await router_agent.process(input_text=message)

        meta_event = {
            "type": "metadata",
            "session_id": session_id,
            "route": decision.route,
        }
        yield f"data: {json.dumps(meta_event)}\n\n"

        if decision.action_name or decision.route == "ACTION":
            action_res = await action_agent.process(
                input_text=message,
                action_name=decision.action_name,
                action_args=decision.action_args,
            )
            data_event = {
                "type": "content",
                "delta": action_res.message,
                "action": {"name": action_res.action_name, "data": action_res.data},
            }
            yield f"data: {json.dumps(data_event)}\n\n"
        else:
            async for token in knowledge_agent.process_stream(input_text=message):
                chunk_event = {"type": "content", "delta": token}
                yield f"data: {json.dumps(chunk_event)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    router_agent: RouterAgent = Depends(get_router_agent),
    knowledge_agent: KnowledgeAgent = Depends(get_knowledge_agent),
    action_agent: ActionAgent = Depends(get_action_agent),
) -> None:
    """WebSocket Connection Endpoint."""
    await websocket.accept()
    session_id = f"ws_sess_{uuid.uuid4().hex[:12]}"

    try:
        await websocket.send_json({"type": "connected", "session_id": session_id})

        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                user_msg = payload.get("message", "")
            except json.JSONDecodeError:
                user_msg = data

            if not user_msg.strip():
                continue

            decision = await router_agent.process(input_text=user_msg)
            await websocket.send_json({"type": "start", "route": decision.route})

            if decision.route == "ACTION":
                action_res = await action_agent.process(input_text=user_msg, action_name=decision.action_name)
                await websocket.send_json({
                    "type": "content",
                    "delta": action_res.message,
                    "action": {"name": action_res.action_name, "data": action_res.data},
                })
            else:
                async for token in knowledge_agent.process_stream(input_text=user_msg):
                    await websocket.send_json({"type": "content", "delta": token})

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
