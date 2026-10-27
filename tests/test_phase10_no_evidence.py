import json
from pathlib import Path

from finance_copilot.adapters.embedding import FakeEmbeddingAdapter
from finance_copilot.adapters.vector_store import FakeVectorStoreAdapter
from finance_copilot.bootstrap import build_policy_qa_service
from finance_copilot.core.document_processing import load_markdown
from finance_copilot.core.schemas.common import SourceReference
from finance_copilot.modules.policy_qa.rules import (
    evidence_support_checker,
    retrieval_confidence_gate,
)
from finance_copilot.modules.policy_qa.schemas import PolicyDocument
from finance_copilot.modules.policy_qa.workflow import PolicyQAWorkflow


POLICY_ROOT = Path("data/poc_datasets/policy_qa")


def _documents() -> list[PolicyDocument]:
    return [
        PolicyDocument(document_id=path.stem, title=path.stem, content=load_markdown(path))
        for path in sorted(POLICY_ROOT.glob("sample_policy_*.md"))
    ]


def test_evidence_checker_rejects_condition_mismatch_without_test_id_logic() -> None:
    source = SourceReference(
        document_id="travel",
        title="合成差旅制度",
        excerpt="普通员工因公前往上海出差时，住宿标准上限为每晚 500 元。",
        score=0.99,
    )
    rejected = evidence_support_checker("北京地区普通员工住宿标准是多少？", [source])
    accepted = evidence_support_checker("上海普通员工住宿标准是多少？", [source])
    assert rejected.supported is False
    assert "北京" in rejected.missing_conditions
    assert "RAG_UNSUPPORTED_CLAIM" in rejected.reasons
    assert accepted.supported is True


def test_retrieval_gate_requires_score_and_direct_support() -> None:
    high = SourceReference(document_id="d", title="t", excerpt="上海住宿标准", score=0.9)
    low = high.model_copy(update={"score": 0.2})
    support = evidence_support_checker("上海住宿标准？", [high])
    assert retrieval_confidence_gate([high], support, threshold=0.55) is True
    assert retrieval_confidence_gate([low], support, threshold=0.55) is False


def test_hybrid_confidence_keeps_threshold_without_over_refusing() -> None:
    source = SourceReference(
        document_id="travel",
        title="合成制度",
        excerpt="总监级员工前往上海出差时，住宿标准上限为每晚 800 元。",
        score=0.535,
    )
    support = evidence_support_checker("总监级员工去上海出差的住宿标准是多少？", [source])
    assert support.best_lexical_score > 0.58
    assert retrieval_confidence_gate([source], support, threshold=0.55) is True


def test_policy_005_regression_and_generic_unknown_city(tmp_path: Path) -> None:
    cases = json.loads((POLICY_ROOT / "test_questions.json").read_text(encoding="utf-8"))["questions"]
    policy_005 = next(case for case in cases if case["test_id"] == "POLICY-005")
    service = build_policy_qa_service(vector_db_path=tmp_path / "vectors.db")
    service.ingest_documents(_documents())

    regression = service.answer_question(policy_005["question"])
    generic = service.answer_question("深圳地区普通员工住宿标准是多少？")
    for response in (regression, generic):
        assert response.agent_recommendation.value == "needs_review"
        assert response.requires_human_review is True
        assert "未在当前财务制度中找到" in response.summary
        assert any("EVIDENCE_CONDITION_MISMATCH" in item for item in response.findings)


def test_unsupported_evidence_never_calls_llm() -> None:
    class ExplodingLLM:
        active_provider = "test"

        def generate(self, prompt: str) -> str:
            raise AssertionError("unsupported evidence must not reach LLM")

    workflow = PolicyQAWorkflow(
        embedding=FakeEmbeddingAdapter(),
        vector_store=FakeVectorStoreAdapter(),
        llm=ExplodingLLM(),
    )
    workflow.ingest_documents(
        [PolicyDocument(document_id="d", title="制度", content="上海普通员工住宿标准 500 元")]
    )
    response = workflow.answer_question("北京地区普通员工住宿标准？")
    assert response.agent_recommendation.value == "needs_review"
