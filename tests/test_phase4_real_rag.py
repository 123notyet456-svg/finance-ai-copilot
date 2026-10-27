import json
from pathlib import Path
from types import SimpleNamespace

from finance_copilot.adapters.embedding import FakeEmbeddingAdapter
from finance_copilot.adapters.llm import FakeLLMAdapter
from finance_copilot.adapters.provider import (
    FallbackEmbeddingAdapter,
    FallbackLLMAdapter,
    OpenAIEmbeddingAdapter,
    OpenAILLMAdapter,
)
from finance_copilot.adapters.vector_store import SQLiteVectorStoreAdapter
from finance_copilot.bootstrap.container import build_policy_qa_service
from finance_copilot.core.document_processing import load_markdown
from finance_copilot.modules.policy_qa.schemas import PolicyDocument
from finance_copilot.modules.policy_qa.workflow import PolicyQAWorkflow


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = self
        self.responses = self

    def create(self, *, model: str, input: object, encoding_format: str | None = None):
        if encoding_format:
            values = input if isinstance(input, list) else [input]
            return SimpleNamespace(
                data=[SimpleNamespace(index=i, embedding=[float(i + 1), 1.0]) for i, _ in enumerate(values)]
            )
        return SimpleNamespace(output_text=f"provider answer via {model}")


class _FailingEmbedding:
    provider_name = "broken"

    def embed(self, texts):
        raise TimeoutError("synthetic timeout")


class _FailingLLM:
    provider_name = "broken"

    def generate(self, prompt):
        raise TimeoutError("synthetic timeout")


def test_openai_adapters_use_sdk_contract_without_network() -> None:
    client = _FakeOpenAIClient()
    embeddings = OpenAIEmbeddingAdapter(client=client).embed(["甲", "乙"])
    answer = OpenAILLMAdapter(client=client, model="test-model").generate("合成问题")
    assert embeddings == [[1.0, 1.0], [2.0, 1.0]]
    assert answer == "provider answer via test-model"


def test_provider_failures_automatically_fallback() -> None:
    embedding = FallbackEmbeddingAdapter(_FailingEmbedding(), FakeEmbeddingAdapter())
    llm = FallbackLLMAdapter(_FailingLLM(), FakeLLMAdapter())
    assert embedding.embed(["合成文本"])
    assert "人工复核" in llm.generate("合成提示")
    assert embedding.fallback_used is True
    assert llm.fallback_used is True
    assert embedding.last_error == "TimeoutError"


def test_sqlite_vector_store_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "vectors.db"
    first = SQLiteVectorStoreAdapter(path)
    first.upsert(["doc:0"], ["上海住宿上限 500 元"], [[1.0, 0.0]], [{"title": "差旅"}])
    second = SQLiteVectorStoreAdapter(path)
    result = second.query([1.0, 0.0], top_k=1)
    assert second.count() == 1
    assert result[0]["id"] == "doc:0"
    assert result[0]["score"] == 1.0


def test_missing_key_selects_fake_fallback_and_persistent_rag(tmp_path: Path) -> None:
    service = build_policy_qa_service(
        vector_db_path=tmp_path / "vectors.db", provider="openai", api_key=""
    )
    service.ingest_documents(
        [PolicyDocument(document_id="travel", title="合成差旅", content="上海住宿上限为 500 元。")]
    )
    response = service.answer_question("上海住宿上限是多少？")
    status = service.runtime_status()
    assert response.sources
    assert status["embedding_fallback_used"] is True
    assert status["llm_fallback_used"] is True
    assert status["vector_store"] == "sqlite"


def test_synthetic_policy_baseline_runs(tmp_path: Path) -> None:
    root = Path("data/poc_datasets/policy_qa")
    documents = [
        PolicyDocument(document_id=path.stem, title=path.stem, content=load_markdown(path))
        for path in sorted(root.glob("sample_policy_*.md"))
    ]
    questions = json.loads((root / "test_questions.json").read_text(encoding="utf-8"))["questions"]
    service = build_policy_qa_service(vector_db_path=tmp_path / "baseline.db")
    assert service.ingest_documents(documents) >= 2
    for case in questions[:4]:
        response = service.answer_question(case["question"])
        assert response.sources
        assert response.module == "policy_qa"


def test_low_relevance_routes_to_human_review() -> None:
    class LowScoreStore:
        provider_name = "test"

        def upsert(self, ids, texts, embeddings, metadatas):
            return None

        def query(self, embedding, top_k=5):
            return [{"id": "x", "text": "不相关", "metadata": {}, "score": 0.1}]

    workflow = PolicyQAWorkflow(
        embedding=FakeEmbeddingAdapter(),
        vector_store=LowScoreStore(),
        llm=FakeLLMAdapter(),
        relevance_threshold=0.55,
    )
    result = workflow.answer_question("任意问题")
    assert result.requires_human_review is True
    assert result.agent_recommendation.value == "needs_review"

