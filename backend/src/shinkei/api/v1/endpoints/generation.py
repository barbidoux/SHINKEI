"""AI Generation API endpoints."""
from typing import Annotated, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from shinkei.auth.dependencies import get_current_user
from shinkei.models.user import User
from shinkei.generation.service import GenerationService
from shinkei.generation.base import GenerationResponse
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class GenerateRequest(BaseModel):
    """Request model for generation endpoint."""
    template_name: str
    context: Dict[str, Any]
    provider: Optional[str] = "openai"
    model: Optional[str] = None
    temperature: float = 0.7


@router.post("/generate", response_model=GenerationResponse)
async def generate_content(
    request: GenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> GenerationResponse:
    """
    Generate content using AI.
    """
    try:
        service = GenerationService(provider=request.provider)
        response = await service.generate_from_template(
            template_name=request.template_name,
            context=request.context,
            model_override=request.model,
            temperature=request.temperature
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Generation failed")
