from pathlib import Path

from finance_copilot.adapters.persistence import SQLiteRepository
from finance_copilot.bootstrap import build_evaluation_service
from finance_copilot.evaluation.schemas import (
    FailureCaseRecord,
    HumanReviewRecord,
    TestOutcome as Outcome,
    TestRecord as POCRecord,
)


def _test_record() -> POCRecord:
    return POCRecord(
        test_id="POLICY-PERSIST-001",
        module="policy_qa",
        sample_category="synthetic",
        input_sample="合成问题",
        expected_result="合成答案",
        agent_output={"summary": "合成输出"},
        outcome=Outcome.PASS,
    )


def test_sqlite_repository_persists_and_upserts(tmp_path: Path) -> None:
    path = tmp_path / "records.db"
    first = SQLiteRepository(path)
    assert first.save("tests", {"id": "T-1", "value": 1}) == "T-1"
    first.save("tests", {"id": "T-1", "value": 2})
    second = SQLiteRepository(path)
    assert second.count("tests") == 1
    assert second.list("tests")[0]["value"] == 2


def test_poc_service_saves_all_record_types_and_exports(tmp_path: Path) -> None:
    service = build_evaluation_service(database_path=tmp_path / "poc.db")
    service.save_test(_test_record())
    service.save_review(
        HumanReviewRecord(
            review_id="REV-001",
            test_id="POLICY-PERSIST-001",
            reviewer="合成评审人",
            original_recommendation="warning",
            review_decision="confirmed",
        )
    )
    service.save_failure(
        FailureCaseRecord(
            failure_id="FAIL-001",
            test_id="POLICY-PERSIST-001",
            input_fingerprint="0" * 64,
            expected_output="有依据",
            actual_output="无依据",
            user_impact="合成风险",
            severity="high",
            root_cause="RAG_NO_EVIDENCE",
            reproducible=True,
            manual_workaround="人工复核",
            improvement_plan="增加回归测试",
        )
    )
    assert service.list_tests()[0].test_id == "POLICY-PERSIST-001"
    assert service.list_reviews()[0].review_id == "REV-001"
    assert service.list_failures()[0].failure_id == "FAIL-001"

    paths = service.export_all(tmp_path / "exports")
    assert all(path.exists() for path in paths.values())
    assert "POLICY-PERSIST-001" in paths["markdown"].read_text(encoding="utf-8")
    assert "REV-001" in paths["reviews_csv"].read_text(encoding="utf-8-sig")
    assert "FAIL-001" in paths["failures_json"].read_text(encoding="utf-8")
