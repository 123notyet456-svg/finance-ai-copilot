"""所有 Agent 对外返回的公共结果协议。"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class AgentRecommendation(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    REJECT = "reject"
    NEEDS_REVIEW = "needs_review"
    NOT_APPLICABLE = "not_applicable"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    OVERRIDDEN = "overridden"


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    title: str
    excerpt: str
    page: int | None = None
    score: float | None = Field(default=None, ge=0, le=1)


class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    module: str
    execution_status: ExecutionStatus = ExecutionStatus.SUCCESS
    agent_recommendation: AgentRecommendation
    review_status: ReviewStatus = ReviewStatus.PENDING
    summary: str
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    requires_human_review: bool = True
    model_version: str = "fake-llm-v1"
    prompt_version: str = "v0.1"
    rules_version: str = "v0.1"
    schema_version: str = "v0.1"
    latency_ms: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0.0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

