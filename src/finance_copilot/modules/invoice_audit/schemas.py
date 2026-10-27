from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class InvoiceInput(BaseModel):
    invoice_number: str | None = None
    invoice_date: date | None = None
    buyer_name: str | None = None
    seller_name: str | None = None
    amount: Decimal | None = None
    tax: Decimal | None = None
    total_amount: Decimal | None = None


class InvoiceRuleConfig(BaseModel):
    valid_days: int = 180
    amount_warning_threshold: Decimal = Decimal("5000")
    amount_review_threshold: Decimal = Decimal("10000")
    amount_tolerance: Decimal = Decimal("0.01")
    company_names: frozenset[str] = frozenset(
        {"虚构科技有限公司", "虚构科技", "虚构公司"}
    )


class InvoiceFinding(BaseModel):
    code: str
    severity: str
    message: str
