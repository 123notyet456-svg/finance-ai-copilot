from datetime import date
import json
from pathlib import Path

from finance_copilot.bootstrap import build_invoice_audit_service
from finance_copilot.modules.invoice_audit.service import InvoiceAuditService


TODAY = date(2026, 6, 29)
SAMPLE_DIR = Path("data/poc_datasets/invoice_audit")


def _load(name: str) -> dict[str, object]:
    return json.loads((SAMPLE_DIR / name).read_text(encoding="utf-8"))


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "invoice_number": "SYNTHETIC-VALID-001",
        "invoice_date": "2026-06-01",
        "buyer_name": "虚构科技有限公司",
        "seller_name": "合成服务有限公司",
        "amount": "94.34",
        "tax": "5.66",
        "total_amount": "100.00",
    }
    payload.update(overrides)
    return payload


def test_normal_sample_passes(tmp_path: Path) -> None:
    result = build_invoice_audit_service(database_path=tmp_path / "normal.db").audit_invoice(
        _load("sample_invoice_normal.json"), today=TODAY
    )
    assert result.agent_recommendation.value == "pass"
    assert result.requires_human_review is False
    assert "不是最终审批" in result.summary


def test_abnormal_sample_rejects_as_agent_suggestion(tmp_path: Path) -> None:
    result = build_invoice_audit_service(database_path=tmp_path / "abnormal.db").audit_invoice(
        _load("sample_invoice_abnormal.json"), today=TODAY
    )
    assert result.agent_recommendation.value == "reject"
    assert result.requires_human_review is True
    assert any(item.startswith("DATE_EXPIRED") for item in result.findings)
    assert any(item.startswith("BUYER_MISMATCH") for item in result.findings)


def test_edge_review_threshold_routes_to_review(tmp_path: Path) -> None:
    result = build_invoice_audit_service(database_path=tmp_path / "edge.db").audit_invoice(
        _load("sample_invoice_edge.json"), today=TODAY
    )
    assert result.agent_recommendation.value == "needs_review"
    assert any(item.startswith("AMOUNT_REVIEW_THRESHOLD") for item in result.findings)


def test_duplicate_is_detected_on_second_audit(tmp_path: Path) -> None:
    service = build_invoice_audit_service(database_path=tmp_path / "duplicate.db")
    first = service.audit_invoice(_valid_payload(), today=TODAY)
    second = service.audit_invoice(_valid_payload(), today=TODAY)
    assert first.agent_recommendation.value == "pass"
    assert second.agent_recommendation.value == "needs_review"
    assert any(item.startswith("DUPLICATE_SUSPECTED") for item in second.findings)


def test_future_missing_nonpositive_and_calculation_rules() -> None:
    service = InvoiceAuditService()
    future = service.audit_invoice(_valid_payload(invoice_date="2026-07-01"), today=TODAY)
    missing = service.audit_invoice({"invoice_number": "SYNTHETIC-MISSING"}, today=TODAY)
    nonpositive = service.audit_invoice(
        _valid_payload(amount="0", tax="0", total_amount="0"), today=TODAY
    )
    mismatch = service.audit_invoice(_valid_payload(total_amount="101.00"), today=TODAY)
    assert future.agent_recommendation.value == "reject"
    assert missing.agent_recommendation.value == "needs_review"
    assert nonpositive.agent_recommendation.value == "reject"
    assert mismatch.agent_recommendation.value == "reject"


def test_warning_threshold_alias_normalization_and_tolerance() -> None:
    service = InvoiceAuditService()
    warning = service.audit_invoice(
        _valid_payload(
            invoice_number="  SYNTHETIC-WARN-001  ",
            buyer_name="虚构科技",
            amount="5,660.38",
            tax="339.62",
            total_amount="6000.00",
        ),
        today=TODAY,
    )
    tolerance = service.audit_invoice(
        _valid_payload(invoice_number="SYNTHETIC-TOL", total_amount="100.01"), today=TODAY
    )
    normalized = service.normalize_invoice(
        _valid_payload(invoice_number="  SYNTHETIC-NORM  ", amount="1,000.00")
    )
    assert warning.agent_recommendation.value == "warning"
    assert tolerance.agent_recommendation.value == "pass"
    assert normalized.invoice_number == "SYNTHETIC-NORM"
    assert str(normalized.amount) == "1000.00"

