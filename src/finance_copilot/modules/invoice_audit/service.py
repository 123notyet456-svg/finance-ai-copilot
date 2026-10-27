from datetime import date

from finance_copilot.core.schemas.common import AgentResponse
from finance_copilot.modules.invoice_audit.schemas import InvoiceInput
from finance_copilot.modules.invoice_audit.workflow import InvoiceAuditWorkflow


class InvoiceAuditService:
    def __init__(self, workflow: InvoiceAuditWorkflow | None = None) -> None:
        self._workflow = workflow or InvoiceAuditWorkflow()

    def normalize_invoice(self, invoice: dict[str, object]) -> InvoiceInput:
        return self._workflow.normalize(invoice)

    def audit_invoice(
        self,
        invoice: dict[str, object] | None = None,
        *,
        today: date | None = None,
    ) -> AgentResponse:
        payload = invoice or {
            "invoice_number": "SYNTHETIC-001",
            "invoice_date": (today or date.today()).isoformat(),
            "buyer_name": "虚构科技有限公司",
            "seller_name": "合成服务有限公司",
            "amount": "100.00",
            "tax": "6.00",
            "total_amount": "106.00",
        }
        return self._workflow.audit(payload, today=today)


def audit_invoice(invoice: dict[str, object] | None = None) -> AgentResponse:
    return InvoiceAuditService().audit_invoice(invoice)
