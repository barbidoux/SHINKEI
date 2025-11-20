"""Application configuration management."""
from typing import Literal
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    
    # Application
    app_name: str = "Shinkei"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://shinkei_user:shinkei_pass_dev_only@localhost:5432/shinkei"
    )
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT encoding (MUST be changed in production)",
        min_length=32
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm (HS256, HS384, or HS512)"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration time in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="JWT refresh token expiration time in days"
    )
    password_min_length: int = Field(
        default=12,
        description="Minimum password length for security"
    )
    require_password_complexity: bool = Field(
        default=True,
        description="Require passwords to have uppercase, lowercase, numbers, and symbols"
    )
    
    # Supabase
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")
    supabase_jwt_secret: str = Field(default="")
    
    # CORS
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173", "http://localhost:3000", "http://localhost:5174", "http://localhost:5175",
            "http://127.0.0.1:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5174", "http://127.0.0.1:5175"
        ],
        description="Allowed CORS origins for frontend applications"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow cookies and authorization headers in CORS requests"
    )
    cors_max_age: int = Field(
        default=600,
        description="Maximum time (in seconds) browsers should cache CORS preflight responses"
    )
    
    # AI/LLM
    default_llm_provider: str = "openai"
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama server host URL (can be local or remote)"
    )
    ollama_default_model: str = Field(
        default="llama3",
        description="Default Ollama model to use for generation"
    )
    
    # Observability
    enable_telemetry: bool = False
    otel_endpoint: str = Field(default="")
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000


settings = Settings()
