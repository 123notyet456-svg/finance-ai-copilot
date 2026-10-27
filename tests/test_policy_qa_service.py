from pathlib import Path

from finance_copilot.core.schemas.common import AgentResponse
from finance_copilot.bootstrap.container import build_policy_qa_service
from finance_copilot.modules.policy_qa.schemas import PolicyDocument


def test_policy_service_returns_common_protocol(tmp_path: Path) -> None:
    service = build_policy_qa_service(vector_db_path=tmp_path / "vectors.db")
    service.ingest_documents(
        [PolicyDocument(document_id="travel", title="合成差旅制度", content="上海住宿上限为每晚 500 元。")] 
    )
    result = service.answer_question("上海住宿标准是多少？")
    assert isinstance(result, AgentResponse)
    assert result.module == "policy_qa"
    assert result.sources
