"""依赖 Port 的轻量 Policy QA RAG 工作流。"""

from dataclasses import dataclass

from finance_copilot.core.ports import EmbeddingPort, LLMPort, VectorStorePort
from finance_copilot.core.schemas.common import (
    AgentRecommendation,
    AgentResponse,
    SourceReference,
)
from finance_copilot.modules.policy_qa.prompts import build_answer_prompt
from finance_copilot.modules.policy_qa.rules import (
    evidence_support_checker,
    retrieval_confidence_gate,
)
from finance_copilot.modules.policy_qa.schemas import PolicyDocument


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    title: str
    content: str
    chunk_index: int


def split_documents(
    documents: list[PolicyDocument],
    *,
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap 必须大于等于 0 且小于 chunk_size")

    chunks: list[DocumentChunk] = []
    step = chunk_size - overlap
    for document in documents:
        content = document.content.strip()
        for index, start in enumerate(range(0, len(content), step)):
            piece = content[start : start + chunk_size].strip()
            if not piece:
                continue
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document.document_id}:{index}",
                    document_id=document.document_id,
                    title=document.title,
                    content=piece,
                    chunk_index=index,
                )
            )
            if start + chunk_size >= len(content):
                break
    return chunks


class PolicyQAWorkflow:
    def __init__(
        self,
        *,
        embedding: EmbeddingPort,
        vector_store: VectorStorePort,
        llm: LLMPort,
        relevance_threshold: float = 0.55,
    ) -> None:
        self._embedding = embedding
        self._vector_store = vector_store
        self._llm = llm
        self._relevance_threshold = relevance_threshold

    def runtime_status(self) -> dict[str, object]:
        return {
            "embedding_provider": getattr(self._embedding, "active_provider", "configured"),
            "embedding_fallback_used": bool(
                getattr(self._embedding, "fallback_used", False)
            ),
            "llm_provider": getattr(self._llm, "active_provider", "configured"),
            "llm_fallback_used": bool(getattr(self._llm, "fallback_used", False)),
            "vector_store": getattr(self._vector_store, "provider_name", "configured"),
        }

    def ingest_documents(self, documents: list[PolicyDocument]) -> int:
        chunks = split_documents(documents)
        reset = getattr(self._vector_store, "reset", None)
        if callable(reset):
            reset()
        if not chunks:
            return 0
        embeddings = self._embedding.embed([chunk.content for chunk in chunks])
        self._vector_store.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            texts=[chunk.content for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "document_id": chunk.document_id,
                    "title": chunk.title,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )
        return len(chunks)

    def answer_question(self, question: str, top_k: int = 5) -> AgentResponse:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("question 不能为空")
        query_embedding = self._embedding.embed([clean_question])[0]
        matches = self._vector_store.query(query_embedding, top_k=top_k)
        sources = [self._to_source(match) for match in matches]
        support = evidence_support_checker(clean_question, sources)
        evidence_accepted = retrieval_confidence_gate(
            sources, support, threshold=self._relevance_threshold
        )
        requires_review = not evidence_accepted

        if not sources:
            summary = "未在当前合成制度中找到明确依据，建议补充制度文件或提交财务人员确认。"
            findings = ["RAG_NO_EVIDENCE: 当前向量库没有可引用的制度片段。"]
        elif not evidence_accepted:
            missing = "、".join(support.missing_conditions) or "问题关键条件"
            summary = (
                "未在当前财务制度中找到能直接支持该问题全部条件的明确依据，"
                "建议补充制度文件或提交财务人员确认。"
            )
            reasons = support.reasons or ("RAG_WRONG_RETRIEVAL",)
            findings = [
                f"{reason}: 检索片段不能直接支持条件：{missing}"
                for reason in reasons
            ]
        else:
            prompt = build_answer_prompt(clean_question, [source.excerpt for source in sources])
            summary = self._llm.generate(prompt)
            findings = [
                f"EVIDENCE_SUPPORTED: 检索到 {len(sources)} 条候选证据，"
                f"最佳词面支持度 {support.best_lexical_score:.2f}。"
            ]

        return AgentResponse(
            module="policy_qa",
            agent_recommendation=(
                AgentRecommendation.NEEDS_REVIEW if requires_review else AgentRecommendation.WARNING
            ),
            summary=summary,
            findings=findings,
            recommendations=["核对来源片段，并由财务人员确认后再执行。"],
            sources=sources,
            next_actions=["无依据、低相关度或冲突时进入人工复核。"],
            requires_human_review=requires_review,
            model_version=f"{getattr(self._llm, 'active_provider', 'configured')}-rag-v1",
        )

    @staticmethod
    def _to_source(match: dict[str, object]) -> SourceReference:
        metadata = match.get("metadata")
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        return SourceReference(
            document_id=str(metadata_dict.get("document_id", match.get("id", "unknown"))),
            title=str(metadata_dict.get("title", "未命名合成制度")),
            excerpt=str(match.get("text", "")),
            score=float(match.get("score", 0.0)),
        )
