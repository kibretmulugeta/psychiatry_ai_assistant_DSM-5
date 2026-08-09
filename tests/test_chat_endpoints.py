"""
Integration tests for Psychiatric Chat, Auth, and Streaming endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_token_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/auth/token endpoint."""
    response = await async_client.post("/api/v1/auth/token", json={"session_id": "test_session_99"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_post_chat_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/chat endpoint for psychiatric tool request."""
    response = await async_client.post(
        "/api/v1/chat",
        json={"message": "Evaluate my PHQ-9 score", "session_id": "test_session_100"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["route"] == "CLINICAL_ASSESSMENT"


@pytest.mark.asyncio
async def test_sse_stream_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/chat/stream SSE endpoint."""
    response = await async_client.get("/api/v1/chat/stream?message=What+are+the+DSM-5+criteria+for+MDD%3F")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    assert "data:" in response.text
