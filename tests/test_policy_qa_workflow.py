from finance_copilot.adapters.embedding import FakeEmbeddingAdapter
from finance_copilot.adapters.llm import FakeLLMAdapter
from finance_copilot.adapters.vector_store import FakeVectorStoreAdapter
from finance_copilot.core.schemas.common import AgentResponse
from finance_copilot.modules.policy_qa.schemas import PolicyDocument
from finance_copilot.modules.policy_qa.workflow import PolicyQAWorkflow


def _workflow() -> PolicyQAWorkflow:
    return PolicyQAWorkflow(
        embedding=FakeEmbeddingAdapter(),
        vector_store=FakeVectorStoreAdapter(),
        llm=FakeLLMAdapter(),
    )


def test_policy_rag_ingests_retrieves_and_returns_sources() -> None:
    workflow = _workflow()
    count = workflow.ingest_documents(
        [PolicyDocument(document_id="travel", title="合成差旅制度", content="上海住宿上限为每晚 500 元。")]
    )
    response = workflow.answer_question("上海住宿标准是多少？")
    assert count == 1
    assert isinstance(response, AgentResponse)
    assert response.sources[0].document_id == "travel"
    assert isinstance(response.requires_human_review, bool)


def test_policy_rag_without_documents_falls_back_to_review() -> None:
    response = _workflow().answer_question("没有制度时如何处理？")
    assert response.sources == []
    assert response.requires_human_review is True
    assert "未在" in response.summary

