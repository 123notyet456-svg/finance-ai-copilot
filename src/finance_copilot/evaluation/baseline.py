"""冻结合成数据集的 POC baseline 执行器。"""

from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from pydantic import BaseModel

from finance_copilot.core.document_processing import load_markdown, sha256_file
from finance_copilot.evaluation.schemas import FailureCaseRecord, TestOutcome, TestRecord
from finance_copilot.evaluation.service import POCRecordService
from finance_copilot.modules.invoice_audit.service import InvoiceAuditService
from finance_copilot.modules.policy_qa.schemas import PolicyDocument
from finance_copilot.modules.policy_qa.service import PolicyQAService


class BaselineSummary(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    policy_total: int
    invoice_total: int
    failure_ids: list[str]


def create_dataset_manifest(dataset_root: str | Path, output_path: str | Path) -> Path:
    root = Path(dataset_root)
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".json"}
        and path.name not in {"README.md", "dataset-manifest.json"}
    )
    payload = {
        "disclaimer": "合成样本 / 非真实数据 / 不可报销",
        "files": [
            {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
            for path in files
        ],
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


class POCBaselineRunner:
    def __init__(
        self,
        *,
        policy_service: PolicyQAService,
        invoice_service: InvoiceAuditService,
        record_service: POCRecordService,
    ) -> None:
        self._policy = policy_service
        self._invoice = invoice_service
        self._records = record_service

    def run(self, dataset_root: str | Path, *, today: date) -> BaselineSummary:
        root = Path(dataset_root)
        outcomes: list[bool] = []
        failure_ids: list[str] = []
        policy_count = self._run_policy(root / "policy_qa", outcomes, failure_ids)
        invoice_count = self._run_invoices(root / "invoice_audit", today, outcomes, failure_ids)
        passed = sum(outcomes)
        return BaselineSummary(
            total=len(outcomes),
            passed=passed,
            failed=len(outcomes) - passed,
            pass_rate=passed / len(outcomes) if outcomes else 0.0,
            policy_total=policy_count,
            invoice_total=invoice_count,
            failure_ids=failure_ids,
        )

    def _run_policy(self, root: Path, outcomes: list[bool], failure_ids: list[str]) -> int:
        documents = [
            PolicyDocument(document_id=path.stem, title=path.stem, content=load_markdown(path))
            for path in sorted(root.glob("sample_policy_*.md"))
        ]
        self._policy.ingest_documents(documents)
        cases = json.loads((root / "test_questions.json").read_text(encoding="utf-8"))["questions"]
        for case in cases:
            response = self._policy.answer_question(case["question"])
            should_refuse = bool(case["should_refuse"])
            passed = (
                response.requires_human_review
                and response.agent_recommendation.value == "needs_review"
                if should_refuse
                else bool(response.sources) and not response.requires_human_review
            )
            record = TestRecord(
                test_id=case["test_id"],
                module="policy_qa",
                sample_category="unsupported" if should_refuse else "answerable",
                input_sample=case["question"],
                expected_result={
                    "expected_keywords": case["expected_keywords"],
                    "should_refuse": should_refuse,
                },
                agent_output=response.model_dump(mode="json"),
                outcome=TestOutcome.PASS if passed else TestOutcome.FAIL,
                failure_reason=None if passed else "拒答或来源门槛未达到",
                root_cause_category=None if passed else "RAG_UNSUPPORTED_CLAIM",
                improvement_action=None if passed else "补充相关度校准与拒答回归测试",
                human_review="pending",
                latency_ms=response.latency_ms,
                estimated_cost=response.estimated_cost,
            )
            self._records.save_test(record)
            outcomes.append(passed)
            if passed:
                self._records.mark_failures_fixed_for_test(record.test_id)
            else:
                failure_ids.append(self._save_failure(record, classify_policy_failure(response)))
        return len(cases)

    def _run_invoices(
        self, root: Path, today: date, outcomes: list[bool], failure_ids: list[str]
    ) -> int:
        expected = {"normal": "pass", "abnormal": "reject", "edge": "needs_review"}
        files = sorted(root.glob("sample_invoice_*.json"))
        for path in files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            category = str(payload["sample_category"])
            response = self._invoice.audit_invoice(payload, today=today)
            passed = response.agent_recommendation.value == expected[category]
            test_id = f"INVOICE-{category.upper()}-001"
            record = TestRecord(
                test_id=test_id,
                module="invoice_audit",
                sample_category=category,
                input_sample=payload,
                expected_result=expected[category],
                agent_output=response.model_dump(mode="json"),
                outcome=TestOutcome.PASS if passed else TestOutcome.FAIL,
                failure_reason=None if passed else "规则建议与冻结预期不一致",
                root_cause_category=None if passed else "RULE_FALSE_POSITIVE",
                improvement_action=None if passed else "复核规则优先级并增加回归测试",
                human_review="pending",
            )
            self._records.save_test(record)
            outcomes.append(passed)
            if passed:
                self._records.mark_failures_fixed_for_test(record.test_id)
            else:
                failure_ids.append(self._save_failure(record, "RULE_FALSE_POSITIVE"))
        return len(files)

    def _save_failure(self, record: TestRecord, root_cause: str) -> str:
        fingerprint = sha256(
            json.dumps(record.input_sample, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        failure_id = f"FAIL-{record.test_id}"
        self._records.save_failure(
            FailureCaseRecord(
                failure_id=failure_id,
                test_id=record.test_id,
                input_fingerprint=fingerprint,
                expected_output=record.expected_result,
                actual_output=record.agent_output,
                user_impact="POC baseline 未达到冻结预期，必须人工复核",
                severity="high",
                root_cause=root_cause,
                reproducible=True,
                manual_workaround="由财务评审人核对合成制度或凭证",
                improvement_plan=record.improvement_action or "增加回归测试",
                regression_test_id=record.test_id,
            )
        )
        return failure_id


def classify_policy_failure(response) -> str:
    """按可观察失败现象分类，不依赖测试 ID。"""
    finding_text = " ".join(response.findings)
    if not response.sources:
        return "RAG_NO_EVIDENCE"
    for category in (
        "RAG_WRONG_RETRIEVAL",
        "RAG_CITATION_MISMATCH",
        "RAG_UNSUPPORTED_CLAIM",
    ):
        if category in finding_text:
            return category
    if response.agent_recommendation.value != "needs_review":
        return "PROMPT_REFUSAL_FAILURE"
    return "TEST_EXPECTATION_AMBIGUOUS"
