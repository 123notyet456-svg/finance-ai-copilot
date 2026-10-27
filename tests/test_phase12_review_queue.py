from pathlib import Path

from finance_copilot.bootstrap import build_evaluation_service
from finance_copilot.evaluation.schemas import TestOutcome as Outcome, TestRecord as POCRecord


def _record(test_id: str, recommendation: str) -> POCRecord:
    return POCRecord(
        test_id=test_id,
        module="policy_qa",
        sample_category="synthetic",
        input_sample="合成输入",
        expected_result="合成预期",
        agent_output={
            "agent_recommendation": recommendation,
            "requires_human_review": recommendation in {"reject", "needs_review"},
            "summary": "Agent 建议",
            "findings": [],
            "sources": [],
        },
        outcome=Outcome.PASS,
    )


def test_pending_review_queue_does_not_fabricate_reviews(tmp_path: Path) -> None:
    service = build_evaluation_service(database_path=tmp_path / "review.db")
    service.save_test(_record("Q-1", "needs_review"))
    service.save_test(_record("Q-2", "reject"))
    service.save_test(_record("Q-3", "pass"))
    assert {record.test_id for record in service.list_pending_human_reviews()} == {"Q-1", "Q-2"}
    assert service.list_reviews() == []

    service.submit_review(
        test_id="Q-1", reviewer="真实评审占位测试", review_decision="confirmed"
    )
    assert [record.test_id for record in service.list_pending_human_reviews()] == ["Q-2"]

    exports = service.export_pending_review_queue(tmp_path / "exports")
    assert all(path.exists() for path in exports.values())
    markdown = exports["markdown"].read_text(encoding="utf-8")
    assert "Q-2" in markdown
    assert "Q-1" not in markdown

