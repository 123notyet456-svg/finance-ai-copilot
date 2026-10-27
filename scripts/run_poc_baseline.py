"""使用冻结合成数据执行可复现 POC baseline。"""

from datetime import date
import json
from pathlib import Path

from finance_copilot.bootstrap import (
    build_evaluation_service,
    build_policy_qa_service,
)
from finance_copilot.evaluation.baseline import POCBaselineRunner
from finance_copilot.modules.invoice_audit.service import InvoiceAuditService


def main() -> None:
    record_service = build_evaluation_service()
    runner = POCBaselineRunner(
        policy_service=build_policy_qa_service(),
        # 冻结 baseline 不读取历史发票库，避免上次运行污染重复检测结果。
        invoice_service=InvoiceAuditService(),
        record_service=record_service,
    )
    summary = runner.run("data/poc_datasets", today=date(2026, 6, 29))
    exports = record_service.export_all(Path("data/exports/baseline"))
    print(json.dumps(summary.model_dump(mode="json"), ensure_ascii=False))
    print(json.dumps({name: str(path) for name, path in exports.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
