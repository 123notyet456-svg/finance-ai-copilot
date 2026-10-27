"""根据结构化 POC 记录生成 Pilot Gate 结论。"""

from pathlib import Path

from pydantic import BaseModel

from finance_copilot.evaluation.schemas import FailureCaseRecord, HumanReviewRecord, TestOutcome, TestRecord


class ModuleMetrics(BaseModel):
    module: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    human_review_required: int
    human_review_completed: int


class PilotGateResult(BaseModel):
    recommendation: str
    overall_pass_rate: float
    modules: list[ModuleMetrics]
    blocking_reasons: list[str]
    conditions: list[str]
    provider_fallback_observed: bool


class PilotGateService:
    POLICY_TARGET = 0.85
    INVOICE_TARGET = 0.90

    def evaluate(
        self,
        records: list[TestRecord],
        failures: list[FailureCaseRecord],
        reviews: list[HumanReviewRecord],
    ) -> PilotGateResult:
        review_test_ids = {
            review.test_id for review in reviews if not review.is_simulated_review
        }
        modules = [
            self._module_metrics(module, records, review_test_ids)
            for module in ("policy_qa", "invoice_audit")
        ]
        total = len(records)
        overall_pass_rate = (
            sum(record.outcome == TestOutcome.PASS for record in records) / total if total else 0.0
        )
        blocking: list[str] = []
        conditions: list[str] = []
        metrics_by_module = {metric.module: metric for metric in modules}

        if not records:
            blocking.append("没有可用于 Pilot Gate 的结构化测试记录")
        if metrics_by_module["policy_qa"].pass_rate < self.POLICY_TARGET:
            blocking.append("Policy QA 通过率低于 85% 门槛")
        if metrics_by_module["invoice_audit"].pass_rate < self.INVOICE_TARGET:
            blocking.append("Invoice Audit 通过率低于 90% 门槛")
        severe_failures = [
            failure for failure in failures
            if failure.severity == "high" and failure.fix_status != "fixed"
        ]
        if severe_failures:
            blocking.append(f"存在 {len(severe_failures)} 个未关闭的高严重度失败")

        review_required = sum(metric.human_review_required for metric in modules)
        review_completed = sum(metric.human_review_completed for metric in modules)
        if review_completed < review_required:
            conditions.append(
                f"人工复核覆盖不足：应复核 {review_required} 项，已完成 {review_completed} 项"
            )

        fallback_observed = any(
            str(record.agent_output.get("model_version", "")).startswith("fake")
            for record in records
        )
        if fallback_observed:
            conditions.append("当前 baseline 使用 Fake Provider fallback，尚未验证真实模型质量、延迟与成本")

        if blocking:
            recommendation = "NO_GO"
        elif conditions:
            recommendation = "CONDITIONAL_GO"
        else:
            recommendation = "GO"
        return PilotGateResult(
            recommendation=recommendation,
            overall_pass_rate=overall_pass_rate,
            modules=modules,
            blocking_reasons=blocking,
            conditions=conditions,
            provider_fallback_observed=fallback_observed,
        )

    @staticmethod
    def _module_metrics(
        module: str,
        records: list[TestRecord],
        review_test_ids: set[str],
    ) -> ModuleMetrics:
        selected = [record for record in records if record.module == module]
        passed = sum(record.outcome == TestOutcome.PASS for record in selected)
        needs_review = [
            record for record in selected
            if record.agent_output.get("requires_human_review") is True
            or record.agent_output.get("agent_recommendation") in {"reject", "needs_review"}
        ]
        return ModuleMetrics(
            module=module,
            total=len(selected),
            passed=passed,
            failed=len(selected) - passed,
            pass_rate=passed / len(selected) if selected else 0.0,
            human_review_required=len(needs_review),
            human_review_completed=sum(record.test_id in review_test_ids for record in needs_review),
        )

    def generate_markdown(self, result: PilotGateResult, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Pilot Gate Review",
            "",
            "> 仅基于合成样本 / 非真实数据；本结论不构成真实财务系统准入或审批。",
            "",
            f"## 结论：{result.recommendation}",
            "",
            f"总体通过率：{result.overall_pass_rate:.2%}",
            "",
            "| 模块 | 样本 | 通过 | 失败 | 通过率 | 应人工复核 | 已人工复核 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        lines.extend(
            f"| {metric.module} | {metric.total} | {metric.passed} | {metric.failed} | "
            f"{metric.pass_rate:.2%} | {metric.human_review_required} | "
            f"{metric.human_review_completed} |"
            for metric in result.modules
        )
        lines.extend(["", "## 阻断原因", ""])
        lines.extend(f"- {reason}" for reason in result.blocking_reasons or ["无"])
        lines.extend(["", "## 条件与未验证项", ""])
        lines.extend(f"- {condition}" for condition in result.conditions or ["无"])
        lines.extend(
            [
                "",
                "## 安全边界",
                "",
                "- 系统不自动审批、不自动拒绝、不自动付款。",
                "- 高风险、无依据、低相关度和冲突结果必须人工复核。",
                "- 当前冻结集规模远低于正式 Pilot 要求，不得外推到真实业务。",
            ]
        )
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output
