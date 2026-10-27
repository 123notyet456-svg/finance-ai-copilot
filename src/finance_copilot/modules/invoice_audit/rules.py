from datetime import date
from decimal import Decimal, InvalidOperation

from finance_copilot.modules.invoice_audit.schemas import (
    InvoiceFinding,
    InvoiceInput,
    InvoiceRuleConfig,
)


REQUIRED_FIELDS = (
    "invoice_number",
    "invoice_date",
    "buyer_name",
    "seller_name",
    "amount",
    "tax",
    "total_amount",
)


def normalize_invoice(payload: dict[str, object]) -> tuple[InvoiceInput, list[InvoiceFinding]]:
    errors: list[InvoiceFinding] = []

    def text(name: str) -> str | None:
        value = payload.get(name)
        normalized = str(value).strip() if value is not None else ""
        return normalized or None

    def decimal(name: str) -> Decimal | None:
        value = payload.get(name)
        if value is None or str(value).strip() == "":
            return None
        try:
            return Decimal(str(value).replace(",", "").strip()).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            errors.append(InvoiceFinding(code=f"INVALID_{name.upper()}", severity="high", message=f"{name} 格式无效"))
            return None

    raw_date = text("invoice_date")
    parsed_date = None
    if raw_date:
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError:
            errors.append(InvoiceFinding(code="INVALID_DATE", severity="high", message="开票日期格式无效"))

    invoice = InvoiceInput(
        invoice_number=text("invoice_number"),
        invoice_date=parsed_date,
        buyer_name=text("buyer_name"),
        seller_name=text("seller_name"),
        amount=decimal("amount"),
        tax=decimal("tax"),
        total_amount=decimal("total_amount"),
    )
    return invoice, errors


def evaluate_invoice_rules(
    invoice: InvoiceInput,
    config: InvoiceRuleConfig,
    *,
    today: date,
    is_duplicate: bool,
) -> list[InvoiceFinding]:
    findings: list[InvoiceFinding] = []
    for field in REQUIRED_FIELDS:
        if getattr(invoice, field) is None:
            findings.append(
                InvoiceFinding(code=f"MISSING_{field.upper()}", severity="high", message=f"缺少必填字段：{field}")
            )

    if invoice.invoice_date is not None:
        age_days = (today - invoice.invoice_date).days
        if age_days < 0:
            findings.append(InvoiceFinding(code="DATE_IN_FUTURE", severity="high", message="开票日期位于未来"))
        elif age_days > config.valid_days:
            findings.append(
                InvoiceFinding(code="DATE_EXPIRED", severity="high", message=f"发票已超过 {config.valid_days} 天有效期")
            )

    if invoice.buyer_name is not None:
        normalized_names = {name.strip().casefold() for name in config.company_names}
        if invoice.buyer_name.casefold() not in normalized_names:
            findings.append(InvoiceFinding(code="BUYER_MISMATCH", severity="high", message="购买方抬头与公司名称或别名不匹配"))

    for name in ("amount", "tax", "total_amount"):
        value = getattr(invoice, name)
        if value is not None and value < Decimal("0"):
            findings.append(InvoiceFinding(code=f"{name.upper()}_NEGATIVE", severity="high", message=f"{name} 不能为负数"))
    if invoice.total_amount is not None and invoice.total_amount == Decimal("0"):
        findings.append(InvoiceFinding(code="TOTAL_NOT_POSITIVE", severity="high", message="价税合计必须为正数"))

    if invoice.amount is not None and invoice.tax is not None and invoice.total_amount is not None:
        difference = abs(invoice.amount + invoice.tax - invoice.total_amount)
        if difference > config.amount_tolerance:
            findings.append(InvoiceFinding(code="TOTAL_MISMATCH", severity="high", message="金额加税额不等于价税合计"))

    if is_duplicate:
        findings.append(InvoiceFinding(code="DUPLICATE_SUSPECTED", severity="high", message="发票号码已存在历史审核记录"))

    if invoice.total_amount is not None:
        if invoice.total_amount >= config.amount_review_threshold:
            findings.append(InvoiceFinding(code="AMOUNT_REVIEW_THRESHOLD", severity="medium", message="金额达到人工复核阈值"))
        elif invoice.total_amount >= config.amount_warning_threshold:
            findings.append(InvoiceFinding(code="AMOUNT_WARNING_THRESHOLD", severity="medium", message="金额达到警告阈值"))
    return findings


def amount_requires_review(amount: Decimal) -> bool:
    return amount >= Decimal("10000")
