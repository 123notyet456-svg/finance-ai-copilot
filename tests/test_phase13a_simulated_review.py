import json
from pathlib import Path

from finance_copilot.bootstrap import build_evaluation_service
from finance_copilot.evaluation.pilot_gate import PilotGateService
from finance_copilot.evaluation.schemas import TestOutcome as Outcome, TestRecord as POCRecord
from scripts.run_simulated_human_review import (
    DISCLAIMER,
    build_simulated_review,
    run_simulated_reviews,
)


def _record(test_id: str, recommendation: str, module: str = "policy_qa") -> POCRecord:
    return POCRecord(
        test_id=test_id,
        module=module,
        sample_category="synthetic",
        input_sample="合成输入",
        expected_result=recommendation,
        agent_output={
            "agent_recommendation": recommendation,
            "requires_human_review": True,
            "summary": "该结果不是最终审批、拒绝或付款动作。",
            "findings": ["SYNTHETIC_RISK: 需要人工复核"],
            "sources": [],
            "model_version": "fake-rag-v1",
        },
        outcome=Outcome.PASS,
    )


def test_actual_pending_items_have_conservative_simulated_distribution() -> None:
    pending = json.loads(
        Path("data/exports/human-review/pending-human-reviews.json").read_text(encoding="utf-8")
    )
    records = [build_simulated_review(item) for item in pending]
    counts = {
        decision: sum(record.human_decision == decision for record in records)
        for decision in ("confirmed", "needs_more_info", "cannot_determine", "overridden")
    }
    assert len(records) == 8
    assert counts == {
        "confirmed": 7,
        "needs_more_info": 0,
        "cannot_determine": 1,
        "overridden": 0,
    }
    assert all(record.is_simulated_review for record in records)
    assert all(record.reviewer_type == "simulated_non_expert" for record in records)
    assert all(DISCLAIMER in record.human_comment for record in records)


def test_simulated_reviews_do_not_mutate_agent_or_complete_real_queue(tmp_path: Path) -> None:
    service = build_evaluation_service(database_path=tmp_path / "reviews.db")
    original = _record("SIM-Q-1", "needs_review")
    service.save_test(original)
    before = service.list_tests()[0].agent_output.copy()
    pending = [
        {
            "test_id": "SIM-Q-1",
            "module": "policy_qa",
            "agent_recommendation": "needs_review",
            "summary": "无明确依据，需人工复核。",
            "findings": ["RAG_NO_EVIDENCE"],
            "sources": [],
        }
    ]
    pending_path = tmp_path / "pending.json"
    pending_path.write_text(json.dumps(pending, ensure_ascii=False), encoding="utf-8")
    records = run_simulated_reviews(
        pending_path,
        tmp_path / "exports",
        tmp_path / "report.md",
        service=service,
    )
    assert service.list_tests()[0].agent_output == before
    assert [record.test_id for record in service.list_pending_human_reviews()] == ["SIM-Q-1"]
    assert service.list_reviews()[0].is_simulated_review is True
    assert DISCLAIMER in (tmp_path / "report.md").read_text(encoding="utf-8")
    assert records[0].source_test_id == "SIM-Q-1"


def test_pilot_gate_ignores_simulated_review_coverage() -> None:
    policy = _record("P-1", "needs_review")
    invoice = _record("I-1", "needs_review", module="invoice_audit")
    simulated = build_simulated_review(
        {
            "test_id": "P-1",
            "module": "policy_qa",
            "agent_recommendation": "needs_review",
            "summary": "需人工复核",
            "findings": ["RAG_NO_EVIDENCE"],
            "sources": [],
        }
    )
    result = PilotGateService().evaluate([policy, invoice], [], [simulated])
    assert result.recommendation == "CONDITIONAL_GO"
    assert any("已完成 0 项" in condition for condition in result.conditions)

