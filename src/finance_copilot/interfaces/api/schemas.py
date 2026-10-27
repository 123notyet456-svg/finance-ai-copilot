"""Versioned HTTP DTOs. Business schemas remain inside their modules."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Recommendation = Literal["pass", "warning", "needs_review", "reject"]
ExecutionStatus = Literal["queued", "processing", "completed", "failed"]
ReviewDecision = Literal["confirmed", "overridden", "unable_to_determine"]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorResponse(APIModel):
    error_code: str
    message: str
    request_id: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class SourceDTO(APIModel):
    document_id: str
    title: str
    excerpt: str
    page: int | None = None
    score: float | None = None


class AgentResultDTO(APIModel):
    request_id: str
    module: str
    execution_status: ExecutionStatus = "completed"
    recommendation: Recommendation
    review_status: str = "pending"
    summary: str
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    sources: list[SourceDTO] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    requires_human_review: bool
    model_version: str
    prompt_version: str
    rules_version: str
    schema_version: str
    latency_ms: int
    estimated_cost: float
    created_at: datetime


class ContextDTO(APIModel):
    app_name: str = "Finance AI Copilot"
    environment: str
    api_version: str = "v1"
    roles: list[str] = Field(default_factory=lambda: ["employee", "finance_reviewer"])
    authentication_mode: str = "demo_role_switch"
    risk_notice: str


class PolicyQuestionRequest(APIModel):
    question: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)


class PolicyRequestDTO(APIModel):
    question: str
    result: AgentResultDTO
    review_id: str | None = None


class PolicyDocumentDTO(APIModel):
    document_id: str
    title: str
    version: str = "v1"
    processing_status: Literal["ready", "disabled", "failed"] = "ready"
    synthetic: bool = True
    source: Literal["builtin", "upload", "api"] = "builtin"
    file_name: str | None = None
    file_type: str | None = None
    content_hash: str | None = None
    chunk_count: int = 0
    uploaded_at: datetime | None = None


class PolicyDocumentCreate(APIModel):
    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    version: str = "v1"


class PolicyDocumentStatusRequest(APIModel):
    processing_status: Literal["ready", "disabled"]


class ConversationCreateRequest(APIModel):
    title: str | None = Field(default=None, max_length=120)


class ConversationMessageRequest(APIModel):
    content: str = Field(min_length=2, max_length=1000)


class ConversationMessageDTO(APIModel):
    message_id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    standalone_question: str | None = None
    result: AgentResultDTO | None = None
    review_id: str | None = None


class ConversationDTO(APIModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageDTO] = Field(default_factory=list)


class ConversationReplyDTO(APIModel):
    conversation_id: str
    user_message: ConversationMessageDTO
    assistant_message: ConversationMessageDTO


class InvoiceAuditRequest(APIModel):
    invoice_number: str
    invoice_date: str
    buyer_name: str
    seller_name: str
    amount: str
    tax: str
    total_amount: str


class ReviewSummaryDTO(APIModel):
    review_id: str
    source_test_id: str
    module: str
    recommendation: str
    summary: str
    risk_level: str
    status: str = "pending"
    created_at: datetime | str | None = None


class ReviewDetailDTO(ReviewSummaryDTO):
    input_sample: dict[str, Any] | str
    findings: list[str] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    agent_output: dict[str, Any]
    decisions: list[dict[str, Any]] = Field(default_factory=list)


class ReviewDecisionRequest(APIModel):
    reviewer: str = Field(min_length=1)
    decision: ReviewDecision
    notes: str = ""
    overridden_recommendation: str | None = None


class MetricsSummaryDTO(APIModel):
    total_tests: int
    passed_tests: int
    overall_pass_rate: float
    pending_reviews: int
    completed_reviews: int
    open_failures: int
    modules: list[dict[str, Any]]
