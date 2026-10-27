from pathlib import Path

import pytest

from finance_copilot.bootstrap import build_evaluation_service
from finance_copilot.evaluation.schemas import TestOutcome as Outcome, TestRecord as POCRecord


def _record() -> POCRecord:
    return POCRecord(
        test_id="HITL-001",
        module="invoice_audit",
        sample_category="synthetic",
        input_sample={"invoice_number": "SYNTHETIC-HITL"},
        expected_result="needs_review",
        agent_output={"agent_recommendation": "needs_review", "summary": "Agent 建议"},
        outcome=Outcome.PASS,
    )


def test_review_is_append_only_and_preserves_agent_output(tmp_path: Path) -> None:
    service = build_evaluation_service(database_path=tmp_path / "hitl.db")
    service.save_test(_record())
    before = service.list_tests()[0].model_dump(mode="json")
    review = service.submit_review(
        test_id="HITL-001",
        reviewer="合成评审人",
        review_decision="overridden",
        overridden_recommendation="warning",
        notes="合成评审备注",
    )
    after = service.list_tests()[0].model_dump(mode="json")
    assert before == after
    assert review.original_recommendation == "needs_review"
    assert service.list_reviews()[0].overridden_recommendation == "warning"


def test_review_validates_target_and_override(tmp_path: Path) -> None:
    service = build_evaluation_service(database_path=tmp_path / "hitl.db")
    with pytest.raises(ValueError, match="不存在"):
        service.submit_review(
            test_id="MISSING", reviewer="x", review_decision="confirmed"
        )
    service.save_test(_record())
    with pytest.raises(ValueError, match="覆盖评审"):
        service.submit_review(
            test_id="HITL-001", reviewer="x", review_decision="overridden"
        )

