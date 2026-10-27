from datetime import date
import json
from pathlib import Path

from finance_copilot.bootstrap import (
    build_evaluation_service,
    build_invoice_audit_service,
    build_policy_qa_service,
)
from finance_copilot.evaluation.baseline import POCBaselineRunner, create_dataset_manifest
from finance_copilot.evaluation.schemas import FailureCaseRecord


def test_dataset_manifest_freezes_synthetic_files(tmp_path: Path) -> None:
    manifest = create_dataset_manifest("data/poc_datasets", tmp_path / "dataset-manifest.json")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["disclaimer"] == "合成样本 / 非真实数据 / 不可报销"
    assert len(payload["files"]) == 6
    assert all(len(item["sha256"]) == 64 for item in payload["files"])


def test_baseline_records_results_failures_and_exports(tmp_path: Path) -> None:
    records = build_evaluation_service(database_path=tmp_path / "poc.db")
    records.save_failure(
        FailureCaseRecord(
            failure_id="FAIL-POLICY-005",
            test_id="POLICY-005",
            input_fingerprint="0" * 64,
            expected_output="needs_review",
            actual_output="warning",
            user_impact="unsupported claim",
            severity="high",
            root_cause="RAG_UNSUPPORTED_CLAIM",
            reproducible=True,
            manual_workaround="人工复核",
            improvement_plan="增加证据门禁",
        )
    )
    runner = POCBaselineRunner(
        policy_service=build_policy_qa_service(vector_db_path=tmp_path / "vectors.db"),
        invoice_service=build_invoice_audit_service(database_path=tmp_path / "invoices.db"),
        record_service=records,
    )
    summary = runner.run("data/poc_datasets", today=date(2026, 6, 29))
    policy_cases = json.loads(
        Path("data/poc_datasets/policy_qa/test_questions.json").read_text(encoding="utf-8")
    )["questions"]
    assert summary.total == len(policy_cases) + 3
    assert summary.policy_total == len(policy_cases)
    assert summary.invoice_total == 3
    assert summary.passed + summary.failed == len(policy_cases) + 3
    assert len(records.list_tests()) == len(policy_cases) + 3
    assert len(
        [failure for failure in records.list_failures() if failure.fix_status != "fixed"]
    ) == summary.failed
    policy_failure = next(
        failure for failure in records.list_failures() if failure.test_id == "POLICY-005"
    )
    assert policy_failure.fix_status == "fixed"
    assert all(path.exists() for path in records.export_all(tmp_path / "exports").values())
