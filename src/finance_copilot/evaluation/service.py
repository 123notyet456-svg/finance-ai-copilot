"""结构化测试记录的本地导出能力。"""

import csv
import json
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from finance_copilot.evaluation.schemas import TestRecord
from finance_copilot.evaluation.schemas import FailureCaseRecord, HumanReviewRecord
from finance_copilot.core.ports import RepositoryPort


class POCRecordService:
    TESTS = "test_records"
    REVIEWS = "human_reviews"
    FAILURES = "failure_cases"

    def __init__(self, repository: RepositoryPort) -> None:
        self._repository = repository

    def save_test(self, record: TestRecord) -> str:
        return self._repository.save(
            self.TESTS, {"id": record.test_id, **record.model_dump(mode="json")}
        )

    def save_review(self, record: HumanReviewRecord) -> str:
        return self._repository.save(
            self.REVIEWS, {"id": record.review_id, **record.model_dump(mode="json")}
        )

    def submit_review(
        self,
        *,
        test_id: str,
        reviewer: str,
        review_decision: str,
        notes: str = "",
        overridden_recommendation: str | None = None,
    ) -> HumanReviewRecord:
        tests = {record.test_id: record for record in self.list_tests()}
        if test_id not in tests:
            raise ValueError(f"测试记录不存在：{test_id}")
        if review_decision not in {"confirmed", "overridden", "unable_to_determine"}:
            raise ValueError("review_decision 无效")
        if review_decision == "overridden" and not overridden_recommendation:
            raise ValueError("覆盖评审必须提供 overridden_recommendation")
        original = str(
            tests[test_id].agent_output.get("agent_recommendation", "not_available")
        )
        record = HumanReviewRecord(
            review_id=f"REV-{uuid4()}",
            test_id=test_id,
            reviewer=reviewer.strip() or "anonymous_reviewer",
            original_recommendation=original,
            review_decision=review_decision,
            overridden_recommendation=overridden_recommendation,
            notes=notes,
        )
        self.save_review(record)
        return record

    def save_failure(self, record: FailureCaseRecord) -> str:
        return self._repository.save(
            self.FAILURES, {"id": record.failure_id, **record.model_dump(mode="json")}
        )

    def mark_failures_fixed_for_test(self, test_id: str) -> int:
        updated = 0
        for failure in self.list_failures():
            if failure.test_id == test_id and failure.fix_status != "fixed":
                self.save_failure(failure.model_copy(update={"fix_status": "fixed"}))
                updated += 1
        return updated

    def list_tests(self) -> list[TestRecord]:
        return [TestRecord.model_validate(self._clean(row)) for row in self._repository.list(self.TESTS)]

    def list_reviews(self) -> list[HumanReviewRecord]:
        return [
            HumanReviewRecord.model_validate(self._clean(row))
            for row in self._repository.list(self.REVIEWS)
        ]

    def list_failures(self) -> list[FailureCaseRecord]:
        return [
            FailureCaseRecord.model_validate(self._clean(row))
            for row in self._repository.list(self.FAILURES)
        ]

    def list_pending_human_reviews(self) -> list[TestRecord]:
        reviewed = {
            record.test_id
            for record in self.list_reviews()
            if not record.is_simulated_review
        }
        return [
            record
            for record in self.list_tests()
            if record.test_id not in reviewed
            and (
                record.agent_output.get("requires_human_review") is True
                or record.agent_output.get("agent_recommendation")
                in {"reject", "needs_review"}
            )
        ]

    def export_pending_review_queue(self, output_dir: str | Path) -> dict[str, Path]:
        directory = Path(output_dir)
        rows = [
            {
                "test_id": record.test_id,
                "module": record.module,
                "sample_category": record.sample_category,
                "agent_recommendation": record.agent_output.get("agent_recommendation"),
                "summary": record.agent_output.get("summary"),
                "findings": record.agent_output.get("findings", []),
                "sources": record.agent_output.get("sources", []),
                "expected_result": record.expected_result,
                "review_status": "pending",
            }
            for record in self.list_pending_human_reviews()
        ]
        json_path = self._save_rows_json(rows, directory / "pending-human-reviews.json")
        csv_path = self._save_rows_csv(rows, directory / "pending-human-reviews.csv")
        markdown_path = directory / "pending-human-reviews.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Pending Human Review Queue",
            "",
            "> 合成样本 / 非真实数据；本文件只收集待办，不代表已经完成人工评审。",
            "",
            "| 测试编号 | 模块 | Agent 建议 | 状态 |",
            "|---|---|---|---|",
        ]
        lines.extend(
            f"| {row['test_id']} | {row['module']} | {row['agent_recommendation']} | pending |"
            for row in rows
        )
        markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"json": json_path, "csv": csv_path, "markdown": markdown_path}

    def export_tests(self, output_dir: str | Path) -> dict[str, Path]:
        from finance_copilot.evaluation.report import generate_markdown_report

        records = self.list_tests()
        directory = Path(output_dir)
        return {
            "json": save_records_json(records, directory / "test-records.json"),
            "csv": save_records_csv(records, directory / "test-records.csv"),
            "markdown": generate_markdown_report(records, directory / "test-report.md"),
        }

    def export_all(self, output_dir: str | Path) -> dict[str, Path]:
        directory = Path(output_dir)
        paths = self.export_tests(directory)
        reviews = [record.model_dump(mode="json") for record in self.list_reviews()]
        failures = [record.model_dump(mode="json") for record in self.list_failures()]
        paths["reviews_json"] = self._save_rows_json(
            reviews, directory / "human-reviews.json"
        )
        paths["reviews_csv"] = self._save_rows_csv(
            reviews, directory / "human-reviews.csv"
        )
        paths["failures_json"] = self._save_rows_json(
            failures, directory / "failure-cases.json"
        )
        paths["failures_csv"] = self._save_rows_csv(
            failures, directory / "failure-cases.csv"
        )
        return paths

    @staticmethod
    def _clean(row: dict[str, object]) -> dict[str, object]:
        return {
            key: value
            for key, value in row.items()
            if key not in {"id", "_stored_at", "_updated_at"}
        }

    @staticmethod
    def _save_rows_json(rows: list[dict[str, object]], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @staticmethod
    def _save_rows_csv(rows: list[dict[str, object]], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(rows[0]) if rows else ["empty"]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        key: json.dumps(value, ensure_ascii=False)
                        if isinstance(value, (dict, list))
                        else value
                        for key, value in row.items()
                    }
                )
        return path


def save_records_json(records: Iterable[TestRecord], path: str | Path) -> Path:
    output_path = _prepare_output(path)
    payload = [record.model_dump(mode="json") for record in records]
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def save_records_csv(records: Iterable[TestRecord], path: str | Path) -> Path:
    output_path = _prepare_output(path)
    rows = [record.model_dump(mode="json") for record in records]
    fieldnames = list(TestRecord.model_fields)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                    for key, value in row.items()
                }
            )
    return output_path


def _prepare_output(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path
