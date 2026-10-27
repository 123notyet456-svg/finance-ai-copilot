from datetime import date

from finance_copilot.core.ports import RepositoryPort
from finance_copilot.core.schemas.common import AgentRecommendation, AgentResponse
from finance_copilot.modules.invoice_audit.rules import evaluate_invoice_rules, normalize_invoice
from finance_copilot.modules.invoice_audit.schemas import InvoiceInput, InvoiceRuleConfig


class InvoiceAuditWorkflow:
    COLLECTION = "audited_invoices"

    def __init__(
        self,
        *,
        repository: RepositoryPort | None = None,
        config: InvoiceRuleConfig | None = None,
    ) -> None:
        self._repository = repository
        self._config = config or InvoiceRuleConfig()

    def normalize(self, payload: dict[str, object]) -> InvoiceInput:
        invoice, _ = normalize_invoice(payload)
        return invoice

    def audit(self, payload: dict[str, object], *, today: date | None = None) -> AgentResponse:
        invoice, normalization_errors = normalize_invoice(payload)
        duplicate = self._is_duplicate(invoice.invoice_number)
        findings = normalization_errors + evaluate_invoice_rules(
            invoice,
            self._config,
            today=today or date.today(),
            is_duplicate=duplicate,
        )
        recommendation = self._recommend(findings)
        requires_review = recommendation != AgentRecommendation.PASS
        if self._repository is not None and invoice.invoice_number:
            self._repository.save(
                self.COLLECTION,
                {
                    "id": invoice.invoice_number,
                    "invoice": invoice.model_dump(mode="json"),
                    "recommendation": recommendation.value,
                },
            )
        finding_text = [f"{finding.code}: {finding.message}" for finding in findings]
        return AgentResponse(
            module="invoice_audit",
            agent_recommendation=recommendation,
            summary=(
                f"合成发票规则审核建议：{recommendation.value}。"
                "该结果不是最终审批、拒绝或付款动作。"
            ),
            findings=finding_text or ["RULES_CLEAR: 未发现基础规则异常"],
            recommendations=["由财务人员核对合成凭证并确认最终业务动作。"],
            next_actions=["如有高风险、重复或阈值命中，进入人工复核。"],
            requires_human_review=requires_review,
            model_version="deterministic-rules-v0.1",
        )

    def _is_duplicate(self, invoice_number: str | None) -> bool:
        if self._repository is None or not invoice_number:
            return False
        return any(row.get("id") == invoice_number for row in self._repository.list(self.COLLECTION))

    @staticmethod
    def _recommend(findings) -> AgentRecommendation:
        codes = {finding.code for finding in findings}
        missing_or_invalid = any(code.startswith(("MISSING_", "INVALID_")) for code in codes)
        reject_codes = {
            "DATE_IN_FUTURE",
            "DATE_EXPIRED",
            "BUYER_MISMATCH",
            "AMOUNT_NEGATIVE",
            "TAX_NEGATIVE",
            "TOTAL_AMOUNT_NEGATIVE",
            "TOTAL_NOT_POSITIVE",
            "TOTAL_MISMATCH",
        }
        if missing_or_invalid:
            return AgentRecommendation.NEEDS_REVIEW
        if codes & reject_codes:
            return AgentRecommendation.REJECT
        if "DUPLICATE_SUSPECTED" in codes or "AMOUNT_REVIEW_THRESHOLD" in codes:
            return AgentRecommendation.NEEDS_REVIEW
        if "AMOUNT_WARNING_THRESHOLD" in codes:
            return AgentRecommendation.WARNING
        return AgentRecommendation.PASS


def audit_placeholder(invoice_number: str, amount) -> AgentResponse:
    payload = {
        "invoice_number": invoice_number,
        "invoice_date": date.today().isoformat(),
        "buyer_name": "虚构科技有限公司",
        "seller_name": "合成服务有限公司",
        "amount": str(amount),
        "tax": "0",
        "total_amount": str(amount),
    }
    return InvoiceAuditWorkflow().audit(payload)
