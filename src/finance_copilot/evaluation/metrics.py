from finance_copilot.evaluation.schemas import TestOutcome, TestRecord


def pass_rate(records: list[TestRecord]) -> float:
    return 0.0 if not records else sum(r.outcome == TestOutcome.PASS for r in records) / len(records)

