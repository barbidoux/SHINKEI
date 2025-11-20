"""Tests for Generation API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from shinkei.main import app
from shinkei.models.user import User
from shinkei.auth.dependencies import get_current_user
from shinkei.config import settings
from shinkei.generation.base import GenerationResponse

@pytest.mark.asyncio(loop_scope="session")
async def test_generate_content():
    """Test generating content via API."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("shinkei.api.v1.endpoints.generation.GenerationService") as MockService:
        mock_service = MockService.return_value
        mock_response = GenerationResponse(
            content="Generated content",
            model_used="test-model"
        )
        mock_service.generate_from_template = AsyncMock(return_value=mock_response)
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/generation/generate",
                    json={
                        "template_name": "generate_story_ideas",
                        "context": {"theme": "Sci-Fi"},
                        "provider": "openai"
                    }
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Generated content"
    assert data["model_used"] == "test-model"

@pytest.mark.asyncio(loop_scope="session")
async def test_generate_content_invalid_template():
    """Test generating content with invalid template."""
    mock_user = User(id="test-user-id", email="me@example.com", name="Me")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with patch("shinkei.api.v1.endpoints.generation.GenerationService") as MockService:
        mock_service = MockService.return_value
        mock_service.generate_from_template = AsyncMock(side_effect=ValueError("Unknown prompt template"))
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    f"{settings.api_v1_prefix}/generation/generate",
                    json={
                        "template_name": "unknown",
                        "context": {}
                    }
                )
        finally:
            app.dependency_overrides = {}
            
    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown prompt template"
