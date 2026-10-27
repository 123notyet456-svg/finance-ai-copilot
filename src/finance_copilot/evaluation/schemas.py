from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class TestOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


class TestRecord(BaseModel):
    test_id: str
    module: str
    sample_category: str
    input_sample: dict[str, object] | str
    expected_result: dict[str, object] | str
    agent_output: dict[str, object]
    outcome: TestOutcome
    failure_reason: str | None = None
    root_cause_category: str | None = None
    improvement_action: str | None = None
    human_review: str | None = None
    latency_ms: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0.0, ge=0)
    tested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumanReviewRecord(BaseModel):
    review_id: str
    test_id: str
    source_test_id: str | None = None
    module: str | None = None
    reviewer: str
    reviewer_name: str | None = None
    reviewer_role: str | None = None
    reviewer_type: str = "human"
    review_scope: str = "business_review"
    original_recommendation: str
    agent_recommendation: str | None = None
    review_decision: str
    human_review_status: str = "completed"
    human_decision: str | None = None
    human_comment: str = ""
    risk_level: str = "medium"
    is_simulated_review: bool = False
    overridden_recommendation: str | None = None
    notes: str = ""
    next_action: str = ""
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FailureCaseRecord(BaseModel):
    failure_id: str
    test_id: str
    input_fingerprint: str
    expected_output: dict[str, object] | str
    actual_output: dict[str, object] | str
    user_impact: str
    severity: str
    root_cause: str
    reproducible: bool
    manual_workaround: str
    improvement_plan: str
    regression_test_id: str | None = None
    fix_status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
