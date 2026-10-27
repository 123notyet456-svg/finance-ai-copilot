"""Phase 13A：作品集用途的模拟 Human-in-the-loop 流程。"""

import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from finance_copilot.bootstrap import build_evaluation_service
from finance_copilot.evaluation.schemas import HumanReviewRecord
from finance_copilot.evaluation.service import POCRecordService


DISCLAIMER = "Simulated review / 模拟评审 / 非真实财务专家确认"
REVIEWER_NAME = "Demo Finance Reviewer"
REVIEWER_ROLE = "Simulated reviewer for portfolio validation"
REVIEWER_TYPE = "simulated_non_expert"
REVIEW_SCOPE = "process validation only"


def has_unauthorized_action_language(item: dict[str, object]) -> bool:
    text = " ".join(
        [str(item.get("summary", "")), *[str(value) for value in item.get("findings", [])]]
    )
    dangerous = (
        "已自动审批",
        "自动批准完成",
        "已自动拒绝",
        "自动付款完成",
        "无需人工确认",
    )
    return any(pattern in text for pattern in dangerous)


def build_simulated_review(
    item: dict[str, object], *, reviewed_at: datetime | None = None
) -> HumanReviewRecord:
    recommendation = str(item["agent_recommendation"])
    findings = list(item.get("findings", []))
    sources = list(item.get("sources", []))
    overreach = has_unauthorized_action_language(item)

    if overreach:
        decision = "overridden"
        comment = f"{DISCLAIMER}：发现疑似越权业务动作措辞，模拟覆盖为 needs_review。"
        risk_level = "critical"
        next_action = "由真实财务与合规评审人复核措辞和业务边界"
        overridden = "needs_review"
    elif recommendation == "needs_review" and findings:
        decision = "confirmed"
        comment = f"{DISCLAIMER}：Agent 已进入 needs_review，且风险原因可追溯；仅确认流程路由有效。"
        risk_level = "medium"
        next_action = "由真实财务评审人独立核对证据并作最终判断"
        overridden = None
    elif not sources:
        decision = "cannot_determine"
        comment = f"{DISCLAIMER}：缺少可核验的原始来源，模拟评审无法确认 Agent 结论。"
        risk_level = "high"
        next_action = "补充原始凭证或证据后交由真实财务评审人判断"
        overridden = None
    else:
        decision = "needs_more_info"
        comment = f"{DISCLAIMER}：当前输出信息不足，需补充上下文和证据。"
        risk_level = "medium"
        next_action = "补充信息后由真实财务评审人重新评审"
        overridden = None

    test_id = str(item["test_id"])
    return HumanReviewRecord(
        review_id=f"SIM-{test_id}-20260630",
        test_id=test_id,
        source_test_id=test_id,
        module=str(item["module"]),
        reviewer=REVIEWER_NAME,
        reviewer_name=REVIEWER_NAME,
        reviewer_role=REVIEWER_ROLE,
        reviewer_type=REVIEWER_TYPE,
        review_scope=REVIEW_SCOPE,
        original_recommendation=recommendation,
        agent_recommendation=recommendation,
        review_decision=decision,
        human_review_status="simulated_completed",
        human_decision=decision,
        human_comment=comment,
        risk_level=risk_level,
        is_simulated_review=True,
        overridden_recommendation=overridden,
        notes=comment,
        next_action=next_action,
        reviewed_at=reviewed_at or datetime.now(timezone.utc),
    )


def run_simulated_reviews(
    pending_path: str | Path,
    output_dir: str | Path,
    report_path: str | Path,
    *,
    service: POCRecordService | None = None,
) -> list[HumanReviewRecord]:
    pending = json.loads(Path(pending_path).read_text(encoding="utf-8"))
    service = service or build_evaluation_service()
    before = _agent_output_hashes(service.list_tests())
    reviewed_at = datetime.now(timezone.utc)
    records = [build_simulated_review(item, reviewed_at=reviewed_at) for item in pending]
    for record in records:
        service.save_review(record)
    after = _agent_output_hashes(service.list_tests())
    if before != after:
        raise RuntimeError("Agent 原始输出发生变化，模拟评审已中止")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [record.model_dump(mode="json") for record in records]
    (output / "simulated-human-reviews.json").write_text(
        json.dumps({"disclaimer": DISCLAIMER, "reviews": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_csv(rows, output / "simulated-human-reviews.csv")
    _write_report(records, Path(report_path), before == after)
    return records


def _agent_output_hashes(records) -> dict[str, str]:
    return {
        record.test_id: sha256(
            json.dumps(record.agent_output, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        for record in records
    }


def _write_csv(rows: list[dict[str, object]], path: Path) -> None:
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


def _write_report(
    records: list[HumanReviewRecord], path: Path, original_outputs_unchanged: bool
) -> None:
    counts = {
        decision: sum(record.human_decision == decision for record in records)
        for decision in ("confirmed", "needs_more_info", "cannot_determine", "overridden")
    }
    lines = [
        "# Simulated Human Review Report",
        "",
        f"> **{DISCLAIMER}**",
        "",
        "本报告仅验证 Human-in-the-loop 流程，不代表真实财务专家意见或企业背书。",
        "",
        "## Reviewer",
        "",
        f"- reviewer_name: {REVIEWER_NAME}",
        f"- reviewer_role: {REVIEWER_ROLE}",
        f"- reviewer_type: {REVIEWER_TYPE}",
        f"- review_scope: {REVIEW_SCOPE}",
        "",
        "## Summary",
        "",
        f"- reviewed: {len(records)}",
        f"- confirmed: {counts['confirmed']}",
        f"- needs_more_info: {counts['needs_more_info']}",
        f"- cannot_determine: {counts['cannot_determine']}",
        f"- overridden: {counts['overridden']}",
        f"- original_agent_outputs_unchanged: {str(original_outputs_unchanged).lower()}",
        "- pilot_gate: CONDITIONAL_GO（模拟评审不计入真实人工复核覆盖率）",
        "",
        "| source_test_id | module | Agent 建议 | 模拟决定 | 风险 |",
        "|---|---|---|---|---|",
    ]
    lines.extend(
        f"| {r.source_test_id} | {r.module} | {r.agent_recommendation} | "
        f"{r.human_decision} | {r.risk_level} |"
        for r in records
    )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"- {DISCLAIMER}",
            "- Human-in-the-loop process validated by simulated review.",
            "- 真实财务评审仍然是进入 Pilot 的前置条件。",
            "- 系统不自动审批、不自动拒绝、不自动付款。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    records = run_simulated_reviews(
        "data/exports/human-review/pending-human-reviews.json",
        "data/exports/human-review",
        "docs/simulated-human-review-report.md",
    )
    counts = {
        decision: sum(record.human_decision == decision for record in records)
        for decision in ("confirmed", "needs_more_info", "cannot_determine", "overridden")
    }
    print(json.dumps({"reviewed": len(records), **counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
