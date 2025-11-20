"""User Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserSettings(BaseModel):
    """User settings schema."""
    language: str = "en"
    ui_theme: str = "system"  # "light", "dark", "system"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    llm_base_url: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    settings: UserSettings = Field(default_factory=UserSettings)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    id: Optional[str] = None  # Will be provided by Supabase Auth


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    model_config = ConfigDict(extra='forbid')
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    settings: Optional[UserSettings] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
