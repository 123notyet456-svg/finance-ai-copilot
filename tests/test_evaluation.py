import json
from pathlib import Path

from finance_copilot.evaluation.report import generate_markdown_report
from finance_copilot.evaluation.schemas import (
    FailureCaseRecord,
    HumanReviewRecord,
    TestOutcome as Outcome,
    TestRecord as EvaluationRecord,
)
from finance_copilot.evaluation.service import save_records_csv, save_records_json


def _record() -> EvaluationRecord:
    return EvaluationRecord(
        test_id="POLICY-001",
        module="policy_qa",
        sample_category="normal",
        input_sample="合成问题",
        expected_result="合成答案",
        agent_output={"summary": "合成输出"},
        outcome=Outcome.PASS,
    )


def test_evaluation_schemas_and_exports(tmp_path: Path) -> None:
    review = HumanReviewRecord(
        review_id="REV-001",
        test_id="POLICY-001",
        reviewer="测试评审人",
        original_recommendation="needs_review",
        review_decision="confirmed",
    )
    failure = FailureCaseRecord(
        failure_id="FAIL-001",
        test_id="POLICY-001",
        input_fingerprint="0" * 64,
        expected_output="有依据回答",
        actual_output="无依据回答",
        user_impact="可能误导",
        severity="high",
        root_cause="RAG_NO_EVIDENCE",
        reproducible=True,
        manual_workaround="人工查阅制度",
        improvement_plan="增加拒答回归测试",
    )
    assert review.review_decision == "confirmed"
    assert failure.reproducible is True

    json_path = save_records_json([_record()], tmp_path / "records.json")
    csv_path = save_records_csv([_record()], tmp_path / "records.csv")
    report_path = generate_markdown_report([_record()], tmp_path / "report.md")
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["test_id"] == "POLICY-001"
    assert "POLICY-001" in csv_path.read_text(encoding="utf-8-sig")
    assert "100.00%" in report_path.read_text(encoding="utf-8")

