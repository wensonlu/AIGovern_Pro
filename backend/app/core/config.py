import os
from typing import Literal


class Settings:
    """应用配置"""

    # FastAPI
    api_version: str = "v1"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 8000))

    # 数据库
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./aigovern.db")
    db_echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # pgvector 配置
    vector_dimensions: int = int(os.getenv("VECTOR_DIMENSIONS", 768))
    vector_similarity_metric: str = os.getenv("VECTOR_SIMILARITY_METRIC", "cosine")

    # LLM 配置
    llm_provider: str = os.getenv("LLM_PROVIDER", "doubao")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model_name: str = os.getenv("LLM_MODEL_NAME", "doubao-pro")
    llm_api_base: str = os.getenv("LLM_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")

    # JWT 认证
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # 文件上传
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", 52428800))  # 50MB
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    allowed_extensions: list[str] = ["pdf", "docx", "txt", "md"]

    # 日志
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
