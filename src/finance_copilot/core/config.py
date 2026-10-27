"""无外部依赖的应用配置。"""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str = os.getenv("FINANCE_COPILOT_ENV", "development")
    log_level: str = os.getenv("FINANCE_COPILOT_LOG_LEVEL", "INFO")
    max_file_size_mb: int = int(os.getenv("FINANCE_COPILOT_MAX_FILE_SIZE_MB", "10"))
    provider: str = os.getenv("FINANCE_COPILOT_PROVIDER", "fake").lower()
    openai_llm_model: str = os.getenv("FINANCE_COPILOT_OPENAI_LLM_MODEL", "gpt-5-mini")
    openai_embedding_model: str = os.getenv(
        "FINANCE_COPILOT_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    vector_db_path: str = os.getenv("FINANCE_COPILOT_VECTOR_DB", "data/policy_vectors.db")
    retrieval_threshold: float = float(
        os.getenv("FINANCE_COPILOT_RETRIEVAL_THRESHOLD", "0.55")
    )


settings = Settings()
