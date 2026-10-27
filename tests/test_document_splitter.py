import pytest

from finance_copilot.modules.policy_qa.schemas import PolicyDocument
from finance_copilot.modules.policy_qa.workflow import split_documents


def test_document_splitter_runs_with_overlap() -> None:
    document = PolicyDocument(document_id="doc", title="合成制度", content="甲乙丙丁戊己庚辛壬癸")
    chunks = split_documents([document], chunk_size=6, overlap=2)
    assert [chunk.content for chunk in chunks] == ["甲乙丙丁戊己", "戊己庚辛壬癸"]
    assert chunks[1].chunk_id == "doc:1"


def test_document_splitter_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        split_documents([], chunk_size=10, overlap=10)

