"""应用组合根：真实 Provider 仅在这里选择，并始终保留 Fake fallback。"""

import os
from pathlib import Path

from finance_copilot.adapters.embedding import FakeEmbeddingAdapter
from finance_copilot.adapters.llm import FakeLLMAdapter
from finance_copilot.adapters.provider import (
    FallbackEmbeddingAdapter,
    FallbackLLMAdapter,
    OpenAIEmbeddingAdapter,
    OpenAILLMAdapter,
)
from finance_copilot.adapters.vector_store import SQLiteVectorStoreAdapter
from finance_copilot.adapters.persistence import SQLiteRepository
from finance_copilot.evaluation.service import POCRecordService
from finance_copilot.evaluation.pilot_gate import PilotGateService
from finance_copilot.modules.invoice_audit.service import InvoiceAuditService
from finance_copilot.modules.invoice_audit.workflow import InvoiceAuditWorkflow
from finance_copilot.modules.policy_qa.service import PolicyQAService
from finance_copilot.modules.policy_qa.workflow import PolicyQAWorkflow


def build_policy_qa_service(
    *,
    vector_db_path: str | Path | None = None,
    provider: str | None = None,
    api_key: str | None = None,
) -> PolicyQAService:
    selected_provider = (provider or os.getenv("FINANCE_COPILOT_PROVIDER", "fake")).lower()
    resolved_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
    primary_embedding = None
    primary_llm = None

    if selected_provider == "openai" and resolved_key:
        try:
            primary_embedding = OpenAIEmbeddingAdapter(
                model=os.getenv(
                    "FINANCE_COPILOT_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
                ),
                api_key=resolved_key,
            )
            primary_llm = OpenAILLMAdapter(
                model=os.getenv("FINANCE_COPILOT_OPENAI_LLM_MODEL", "gpt-5-mini"),
                api_key=resolved_key,
            )
        except Exception:
            primary_embedding = None
            primary_llm = None

    embedding = FallbackEmbeddingAdapter(primary_embedding, FakeEmbeddingAdapter())
    llm = FallbackLLMAdapter(primary_llm, FakeLLMAdapter())
    store = SQLiteVectorStoreAdapter(
        vector_db_path or os.getenv("FINANCE_COPILOT_VECTOR_DB", "data/policy_vectors.db")
    )
    workflow = PolicyQAWorkflow(
        embedding=embedding,
        vector_store=store,
        llm=llm,
        relevance_threshold=float(
            os.getenv("FINANCE_COPILOT_RETRIEVAL_THRESHOLD", "0.55")
        ),
    )
    return PolicyQAService(workflow)


def build_invoice_audit_service(
    *, database_path: str | Path | None = None,
) -> InvoiceAuditService:
    repository = SQLiteRepository(
        database_path or os.getenv("FINANCE_COPILOT_DATABASE", "data/finance_copilot.db")
    )
    return InvoiceAuditService(InvoiceAuditWorkflow(repository=repository))


def build_evaluation_service(
    *, database_path: str | Path | None = None,
) -> POCRecordService:
    repository = SQLiteRepository(
        database_path or os.getenv("FINANCE_COPILOT_DATABASE", "data/finance_copilot.db")
    )
    return POCRecordService(repository)


def build_pilot_gate_service() -> PilotGateService:
    return PilotGateService()
