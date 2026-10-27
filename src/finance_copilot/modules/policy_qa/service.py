from finance_copilot.core.schemas.common import AgentResponse
from finance_copilot.modules.policy_qa.schemas import PolicyDocument
from finance_copilot.modules.policy_qa.workflow import PolicyQAWorkflow


class PolicyQAService:
    """薄服务层；具体基础设施由外部组装并注入。"""

    def __init__(self, workflow: PolicyQAWorkflow) -> None:
        self._workflow = workflow

    def ingest_documents(self, documents: list[PolicyDocument]) -> int:
        return self._workflow.ingest_documents(documents)

    def answer_question(self, question: str, top_k: int = 5) -> AgentResponse:
        return self._workflow.answer_question(question, top_k=top_k)

    def runtime_status(self) -> dict[str, object]:
        return self._workflow.runtime_status()
