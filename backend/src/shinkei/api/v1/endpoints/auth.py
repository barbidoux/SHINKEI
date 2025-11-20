from typing import Annotated
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.config import settings
from shinkei.auth.dependencies import get_db_session
from shinkei.models.user import User
from shinkei.repositories.user import UserRepository
from shinkei.schemas.user import UserCreate

router = APIRouter()

from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(
    login_data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Dev Login endpoint.
    In production, this would be handled by Supabase Auth.
    Here we simulate it by issuing a JWT signed with our local secret.
    """
    repo = UserRepository(session)
    user = await repo.get_by_email(login_data.email)
    
    if not user:
        # Auto-register for dev convenience if it doesn't exist
        user = await repo.create(UserCreate(
            email=login_data.email,
            name=login_data.email.split("@")[0],
            settings={}
        ))
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.utcnow() + access_token_expires
    to_encode = {"sub": str(user.id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}
