from pathlib import Path

from finance_copilot.adapters.embedding import FakeEmbeddingAdapter
from finance_copilot.adapters.llm import FakeLLMAdapter
from finance_copilot.adapters.ocr import FakeOCRAdapter
from finance_copilot.adapters.persistence import FakeRepository
from finance_copilot.adapters.vector_store import FakeVectorStoreAdapter


def test_fake_adapters_are_stable() -> None:
    embeddings = FakeEmbeddingAdapter().embed(["制度样本"])
    assert embeddings == FakeEmbeddingAdapter().embed(["制度样本"])
    assert "人工" in FakeLLMAdapter().generate("上下文")
    assert "非真实" in FakeOCRAdapter().extract_text(Path("sample.png"))

    store = FakeVectorStoreAdapter()
    store.upsert(["1"], ["制度样本"], embeddings, [{"title": "样本"}])
    assert store.query(embeddings[0], top_k=1)[0]["id"] == "1"

    repository = FakeRepository()
    repository.save("tests", {"value": 1})
    assert repository.list("tests")[0]["value"] == 1


def test_fake_llm_extracts_a_concise_supported_answer() -> None:
    prompt = (
        "只能根据以下合成制度上下文回答。\n上下文：\n"
        "虚构公司员工因公前往上海出差时，普通员工住宿标准上限为每晚 500 元，"
        "总监级员工上限为每晚 800 元。\n\n问题：上海出差住宿标准是什么？"
    )

    answer = FakeLLMAdapter().generate(prompt)

    assert answer == (
        "虚构公司员工因公前往上海出差时，普通员工住宿标准上限为每晚 500 元，"
        "总监级员工上限为每晚 800 元。"
    )
