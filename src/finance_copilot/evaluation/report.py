"""Markdown 测试报告生成器。"""

from pathlib import Path
from typing import Iterable

from finance_copilot.evaluation.metrics import pass_rate
from finance_copilot.evaluation.schemas import TestRecord


def generate_markdown_report(records: Iterable[TestRecord], path: str | Path) -> Path:
    record_list = list(records)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# POC 测试报告",
        "",
        "> 本报告由合成样本生成，不代表真实财务结论。",
        "",
        f"- 样本数：{len(record_list)}",
        f"- 通过率：{pass_rate(record_list):.2%}",
        "",
        "| 测试编号 | 模块 | 类别 | 结果 |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| {record.test_id} | {record.module} | {record.sample_category} | {record.outcome.value} |"
        for record in record_list
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path

