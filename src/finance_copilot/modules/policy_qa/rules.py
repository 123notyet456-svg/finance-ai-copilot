"""Policy QA 的确定性证据与检索门禁。"""

from dataclasses import dataclass
from math import sqrt
import re
from typing import Sequence

from finance_copilot.core.schemas.common import SourceReference


CITY_TERMS = frozenset(
    {
        "北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "重庆",
        "武汉", "西安", "苏州", "天津", "长沙", "青岛", "厦门",
    }
)
ROLE_TERMS = frozenset({"普通员工", "总监级员工", "总监", "经理", "员工"})


@dataclass(frozen=True, slots=True)
class EvidenceSupportResult:
    supported: bool
    best_lexical_score: float
    missing_conditions: tuple[str, ...]
    reasons: tuple[str, ...]


def evidence_support_checker(
    question: str,
    sources: Sequence[SourceReference],
    *,
    minimum_lexical_score: float = 0.12,
) -> EvidenceSupportResult:
    """检查是否至少一条引用直接支持问题中的关键条件。"""
    if not sources:
        return EvidenceSupportResult(False, 0.0, (), ("RAG_NO_EVIDENCE",))

    required_conditions = _extract_conditions(question)
    question_terms = _bigrams(_normalize(question))
    best_score = 0.0
    best_missing: tuple[str, ...] = required_conditions

    for source in sources:
        evidence = _normalize(source.excerpt)
        evidence_terms = _bigrams(evidence)
        lexical_score = (
            len(question_terms & evidence_terms) / len(question_terms)
            if question_terms
            else 0.0
        )
        missing = tuple(term for term in required_conditions if _normalize(term) not in evidence)
        if lexical_score > best_score:
            best_score = lexical_score
            best_missing = missing
        if not missing and lexical_score >= minimum_lexical_score:
            return EvidenceSupportResult(True, lexical_score, (), ())

    reasons: list[str] = ["RAG_UNSUPPORTED_CLAIM"]
    if best_missing:
        reasons.append("EVIDENCE_CONDITION_MISMATCH")
    if best_score < minimum_lexical_score:
        reasons.append("RAG_WRONG_RETRIEVAL")
    return EvidenceSupportResult(
        False,
        best_score,
        best_missing,
        tuple(reasons),
    )


def retrieval_confidence_gate(
    sources: Sequence[SourceReference],
    support: EvidenceSupportResult,
    *,
    threshold: float = 0.55,
) -> bool:
    """向量相关度和证据直接支持必须同时通过。"""
    if not sources or not support.supported:
        return False
    top_score = sources[0].score
    if top_score is None:
        return False
    combined_confidence = sqrt(
        max(0.0, top_score) * max(0.0, support.best_lexical_score)
    )
    return combined_confidence >= threshold


def should_require_review(
    has_sources: bool,
    top_score: float | None = None,
    *,
    threshold: float = 0.55,
) -> bool:
    """保留兼容入口；新工作流使用 retrieval_confidence_gate。"""
    return not has_sources or top_score is None or top_score < threshold


def _extract_conditions(question: str) -> tuple[str, ...]:
    normalized = _normalize(question)
    conditions: list[str] = []
    for vocabulary in (CITY_TERMS, ROLE_TERMS):
        matches = [term for term in vocabulary if _normalize(term) in normalized]
        if matches:
            conditions.append(max(matches, key=len))
    for match in re.findall(r"([\u4e00-\u9fff]{2,3})地区", question):
        if match not in conditions:
            conditions.append(match)
    conditions.extend(re.findall(r"\d+(?:\.\d+)?", normalized))
    return tuple(dict.fromkeys(conditions))


def _normalize(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9.]", "", text).casefold()


def _bigrams(text: str) -> set[str]:
    return {text[index : index + 2] for index in range(max(0, len(text) - 1))}
