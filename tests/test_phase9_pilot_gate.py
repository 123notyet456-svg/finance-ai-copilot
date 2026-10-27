from pathlib import Path

from finance_copilot.evaluation.pilot_gate import PilotGateService
from finance_copilot.evaluation.schemas import (
    FailureCaseRecord,
    HumanReviewRecord,
    TestOutcome as Outcome,
    TestRecord as POCRecord,
)


def _record(test_id: str, module: str, outcome: Outcome, recommendation: str) -> POCRecord:
    return POCRecord(
        test_id=test_id,
        module=module,
        sample_category="synthetic",
        input_sample="x",
        expected_result="y",
        agent_output={
            "agent_recommendation": recommendation,
            "requires_human_review": recommendation in {"reject", "needs_review"},
            "model_version": "fake-rag-v1" if module == "policy_qa" else "deterministic-rules-v0.1",
        },
        outcome=outcome,
    )


def test_gate_is_no_go_with_quality_and_safety_blockers(tmp_path: Path) -> None:
    records = [
        *[_record(f"P-{i}", "policy_qa", Outcome.PASS, "warning") for i in range(4)],
        _record("P-5", "policy_qa", Outcome.FAIL, "warning"),
        *[_record(f"I-{i}", "invoice_audit", Outcome.PASS, "pass") for i in range(3)],
    ]
    failures = [
        FailureCaseRecord(
            failure_id="FAIL-P-5",
            test_id="P-5",
            input_fingerprint="0" * 64,
            expected_output="needs_review",
            actual_output="warning",
            user_impact="unsupported claim",
            severity="high",
            root_cause="RAG_UNSUPPORTED_CLAIM",
            reproducible=True,
            manual_workaround="人工复核",
            improvement_plan="增加拒答测试",
        )
    ]
    service = PilotGateService()
    result = service.evaluate(records, failures, [])
    assert result.recommendation == "NO_GO"
    assert result.overall_pass_rate == 0.875
    assert result.modules[0].pass_rate == 0.8
    assert result.provider_fallback_observed is True
    report = service.generate_markdown(result, tmp_path / "gate.md")
    assert "NO_GO" in report.read_text(encoding="utf-8")


def test_gate_can_reach_go_when_all_gates_and_reviews_pass() -> None:
    records = [
        _record("P-1", "policy_qa", Outcome.PASS, "warning"),
        _record("I-1", "invoice_audit", Outcome.PASS, "needs_review"),
    ]
    records[0].agent_output["model_version"] = "openai-rag-v1"
    reviews = [
        HumanReviewRecord(
            review_id="R-1",
            test_id="I-1",
            reviewer="reviewer",
            original_recommendation="needs_review",
            review_decision="confirmed",
        )
    ]
    result = PilotGateService().evaluate(records, [], reviews)
    assert result.recommendation == "GO"

