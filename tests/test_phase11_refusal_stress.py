import json
from pathlib import Path

from finance_copilot.bootstrap import build_policy_qa_service
from finance_copilot.core.document_processing import load_markdown
from finance_copilot.modules.policy_qa.schemas import PolicyDocument


def test_all_frozen_unsupported_questions_refuse_generically(tmp_path: Path) -> None:
    root = Path("data/poc_datasets/policy_qa")
    cases = json.loads((root / "test_questions.json").read_text(encoding="utf-8"))["questions"]
    unsupported = [case for case in cases if case["should_refuse"]]
    service = build_policy_qa_service(vector_db_path=tmp_path / "vectors.db")
    service.ingest_documents(
        [
            PolicyDocument(document_id=path.stem, title=path.stem, content=load_markdown(path))
            for path in sorted(root.glob("sample_policy_*.md"))
        ]
    )
    assert len(unsupported) >= 6
    for case in unsupported:
        response = service.answer_question(case["question"])
        assert response.agent_recommendation.value == "needs_review", case["test_id"]
        assert response.requires_human_review is True
        assert "明确依据" in response.summary

