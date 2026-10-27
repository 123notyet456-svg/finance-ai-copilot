from finance_copilot.core.schemas.common import AgentResponse
from finance_copilot.modules.invoice_audit.service import InvoiceAuditService


def test_invoice_service_returns_common_protocol() -> None:
    result = InvoiceAuditService().audit_invoice(
        {"invoice_number": "SYNTHETIC-001", "total_amount": "100.00"}
    )
    assert isinstance(result, AgentResponse)
    assert result.module == "invoice_audit"
    assert result.estimated_cost == 0

