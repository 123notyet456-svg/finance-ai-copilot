"""FastAPI facade over the existing application services."""

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from finance_copilot.adapters.persistence import SQLiteRepository
from finance_copilot.bootstrap.container import (
    build_evaluation_service,
    build_invoice_audit_service,
    build_pilot_gate_service,
    build_policy_qa_service,
)
from finance_copilot.core.document_processing import load_markdown, parse_uploaded_document
from finance_copilot.core.exceptions import FinanceCopilotError
from finance_copilot.core.schemas.common import AgentResponse
from finance_copilot.evaluation.schemas import TestOutcome, TestRecord
from finance_copilot.modules.policy_qa.schemas import PolicyDocument
from finance_copilot.modules.policy_qa.workflow import split_documents
from finance_copilot.interfaces.api.schemas import (
    AgentResultDTO,
    ContextDTO,
    ConversationCreateRequest,
    ConversationDTO,
    ConversationMessageDTO,
    ConversationMessageRequest,
    ConversationReplyDTO,
    ErrorResponse,
    InvoiceAuditRequest,
    MetricsSummaryDTO,
    PolicyDocumentCreate,
    PolicyDocumentDTO,
    PolicyDocumentStatusRequest,
    PolicyQuestionRequest,
    PolicyRequestDTO,
    ReviewDecisionRequest,
    ReviewDetailDTO,
    ReviewSummaryDTO,
)


RISK_NOTICE = (
    "系统仅提供辅助分析和审核建议；不自动审批、不自动拒绝、不自动付款；"
    "高风险结果必须由授权人员复核。"
)
POLICY_REQUESTS = "api_policy_requests"
POLICY_DOCUMENTS = "api_policy_documents"
INVOICE_AUDITS = "api_invoice_audits"
CONVERSATIONS = "api_conversations"
CONVERSATION_MESSAGES = "api_conversation_messages"


def _database_path() -> str:
    return os.getenv("FINANCE_COPILOT_DATABASE", "data/finance_copilot.db")


def _request_repository() -> SQLiteRepository:
    return SQLiteRepository(_database_path())


def _sample_policy_documents() -> list[PolicyDocument]:
    documents: list[PolicyDocument] = []
    for path in sorted(Path("data/poc_datasets/policy_qa").glob("sample_policy_*.md")):
        content = load_markdown(path)
        title = next(
            (line.removeprefix("# ").strip() for line in content.splitlines() if line.startswith("# ")),
            path.stem,
        )
        documents.append(PolicyDocument(document_id=path.stem, title=title, content=content))
    for row in _request_repository().list(POLICY_DOCUMENTS):
        if row.get("processing_status", "ready") != "ready":
            continue
        documents.append(
            PolicyDocument(
                document_id=str(row["document_id"]),
                title=str(row["title"]),
                content=str(row["content"]),
            )
        )
    return documents


def _agent_result(response: AgentResponse) -> AgentResultDTO:
    payload = response.model_dump(mode="json")
    recommendation = payload.pop("agent_recommendation")
    payload["recommendation"] = recommendation
    payload["execution_status"] = "completed" if payload["execution_status"] == "success" else "failed"
    if recommendation == "not_applicable":
        payload["recommendation"] = "needs_review"
    return AgentResultDTO.model_validate(payload)


def _review_summary(record: TestRecord) -> ReviewSummaryDTO:
    output = record.agent_output
    recommendation = str(output.get("agent_recommendation", "needs_review"))
    return ReviewSummaryDTO(
        review_id=record.test_id,
        source_test_id=record.test_id,
        module=record.module,
        recommendation=recommendation,
        summary=str(output.get("summary", "等待财务复核")),
        risk_level="high" if recommendation == "reject" else "medium",
        created_at=record.tested_at,
    )


def _execute_policy_question(
    question: str,
    *,
    original_question: str | None = None,
    top_k: int = 5,
) -> PolicyRequestDTO:
    service = build_policy_qa_service()
    documents = _sample_policy_documents()
    if not documents:
        raise ValueError("没有可用的制度文档")
    service.ingest_documents(documents)
    response = service.answer_question(question, top_k=top_k)
    result = _agent_result(response)
    review_id: str | None = None
    if result.requires_human_review:
        review_id = f"API-REVIEW-{response.request_id}"
        build_evaluation_service().save_test(
            TestRecord(
                test_id=review_id,
                module="policy_qa",
                sample_category="api_request",
                input_sample={
                    "question": original_question or question,
                    "standalone_question": question,
                },
                expected_result="等待授权财务人员复核",
                agent_output=response.model_dump(mode="json"),
                outcome=TestOutcome.PARTIAL,
                human_review="pending",
                latency_ms=response.latency_ms,
                estimated_cost=response.estimated_cost,
            )
        )
    record = {
        "id": response.request_id,
        "question": original_question or question,
        "standalone_question": question,
        "result": result.model_dump(mode="json"),
        "review_id": review_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _request_repository().save(POLICY_REQUESTS, record)
    return PolicyRequestDTO(
        question=original_question or question,
        result=result,
        review_id=review_id,
    )


def _standalone_question(current: str, previous: str | None) -> str:
    clean = current.strip()
    if not previous:
        return clean
    cities = ("北京", "上海", "广州", "深圳", "杭州", "成都")
    previous_city = next((city for city in cities if city in previous), None)
    current_city = next((city for city in cities if city in clean), None)
    follow_up = len(clean) <= 20 or clean.startswith(("那", "那么", "这个", "它", "还有", "上面"))
    if follow_up and previous_city and current_city and previous_city != current_city:
        return previous.replace(previous_city, current_city)
    if follow_up:
        return f"{previous}；用户追问：{clean}"
    return clean


def _conversation_messages(conversation_id: str) -> list[ConversationMessageDTO]:
    rows = [
        row for row in _request_repository().list(CONVERSATION_MESSAGES)
        if row.get("conversation_id") == conversation_id
    ]
    messages = [
        ConversationMessageDTO.model_validate(
            {key: value for key, value in row.items() if not key.startswith("_") and key != "id"}
        )
        for row in rows
    ]
    return sorted(messages, key=lambda message: message.created_at)


def _conversation(conversation_id: str) -> ConversationDTO:
    row = next(
        (item for item in _request_repository().list(CONVERSATIONS) if item.get("id") == conversation_id),
        None,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return ConversationDTO(
        conversation_id=conversation_id,
        title=str(row["title"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        messages=_conversation_messages(conversation_id),
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Finance AI Copilot API",
        version="0.2.0",
        description="Versioned product interface over the existing POC services.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in os.getenv(
            "FINANCE_COPILOT_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:3100",
        ).split(",")],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        body = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message=str(exc),
            request_id=request_id,
            details={"path": request.url.path},
        )
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))

    @app.exception_handler(FinanceCopilotError)
    async def finance_error_handler(request: Request, exc: FinanceCopilotError) -> JSONResponse:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        body = ErrorResponse(
            error_code="DOCUMENT_PROCESSING_ERROR",
            message=str(exc),
            request_id=request_id,
            details={"path": request.url.path},
        )
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        body = ErrorResponse(
            error_code="REQUEST_VALIDATION_ERROR",
            message="请求参数不符合契约",
            request_id=request_id,
            details={"errors": exc.errors()},
        )
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        body = ErrorResponse(
            error_code="NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR",
            message=str(exc.detail),
            request_id=request_id,
            retryable=False,
            details={"path": request.url.path},
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))

    @app.get("/api/v1/context", response_model=ContextDTO)
    def context() -> ContextDTO:
        return ContextDTO(
            environment=os.getenv("FINANCE_COPILOT_ENV", "local"),
            risk_notice=RISK_NOTICE,
        )

    @app.get("/api/v1/policy/documents", response_model=list[PolicyDocumentDTO])
    def list_policy_documents() -> list[PolicyDocumentDTO]:
        builtins = [
            PolicyDocumentDTO(document_id=document.document_id, title=document.title)
            for path in sorted(Path("data/poc_datasets/policy_qa").glob("sample_policy_*.md"))
            for document in [PolicyDocument(
                document_id=path.stem,
                title=next(
                    (line.removeprefix("# ").strip() for line in load_markdown(path).splitlines() if line.startswith("# ")),
                    path.stem,
                ),
                content=load_markdown(path),
            )]
        ]
        uploaded = [
            PolicyDocumentDTO.model_validate(
                {
                    key: value for key, value in row.items()
                    if key in PolicyDocumentDTO.model_fields
                }
            )
            for row in _request_repository().list(POLICY_DOCUMENTS)
        ]
        return [*builtins, *uploaded]

    @app.post("/api/v1/policy/documents", response_model=PolicyDocumentDTO, status_code=201)
    def create_policy_document(payload: PolicyDocumentCreate) -> PolicyDocumentDTO:
        uploaded_at = datetime.now(timezone.utc)
        chunk_count = len(split_documents([
            PolicyDocument(document_id=payload.document_id, title=payload.title, content=payload.content)
        ]))
        _request_repository().save(
            POLICY_DOCUMENTS,
            {
                "id": payload.document_id,
                **payload.model_dump(),
                "processing_status": "ready",
                "synthetic": False,
                "source": "api",
                "chunk_count": chunk_count,
                "uploaded_at": uploaded_at.isoformat(),
            },
        )
        return PolicyDocumentDTO(
            document_id=payload.document_id,
            title=payload.title,
            version=payload.version,
            synthetic=False,
            source="api",
            chunk_count=chunk_count,
            uploaded_at=uploaded_at,
        )

    @app.post("/api/v1/policy/documents/upload", response_model=PolicyDocumentDTO, status_code=201)
    async def upload_policy_document(
        file: UploadFile = File(...),
        title: str | None = Form(default=None),
        version: str = Form(default="v1"),
    ) -> PolicyDocumentDTO:
        # UploadFile must be read inside the request lifecycle.
        data = await file.read()
        parsed = parse_uploaded_document(file.filename or "uploaded", data)
        document_id = f"DOC-{uuid4()}"
        resolved_title = (title or Path(parsed.file_name).stem).strip()
        if not resolved_title:
            raise ValueError("文档标题不能为空")
        uploaded_at = datetime.now(timezone.utc)
        chunk_count = len(split_documents([
            PolicyDocument(document_id=document_id, title=resolved_title, content=parsed.content)
        ]))
        row = {
            "id": document_id,
            "document_id": document_id,
            "title": resolved_title,
            "version": version.strip() or "v1",
            "content": parsed.content,
            "processing_status": "ready",
            "synthetic": False,
            "source": "upload",
            "file_name": parsed.file_name,
            "file_type": parsed.file_type,
            "content_hash": parsed.content_hash,
            "chunk_count": chunk_count,
            "uploaded_at": uploaded_at.isoformat(),
        }
        _request_repository().save(POLICY_DOCUMENTS, row)
        return PolicyDocumentDTO.model_validate(
            {key: value for key, value in row.items() if key in PolicyDocumentDTO.model_fields}
        )

    @app.patch("/api/v1/policy/documents/{document_id}", response_model=PolicyDocumentDTO)
    def update_policy_document_status(
        document_id: str, payload: PolicyDocumentStatusRequest
    ) -> PolicyDocumentDTO:
        row = next(
            (item for item in _request_repository().list(POLICY_DOCUMENTS) if item.get("id") == document_id),
            None,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="上传文档不存在")
        row["processing_status"] = payload.processing_status
        clean_row = {key: value for key, value in row.items() if not key.startswith("_")}
        clean_row["id"] = document_id
        _request_repository().save(POLICY_DOCUMENTS, clean_row)
        return PolicyDocumentDTO.model_validate(
            {key: value for key, value in row.items() if key in PolicyDocumentDTO.model_fields}
        )

    @app.post("/api/v1/policy/questions", response_model=PolicyRequestDTO, status_code=201)
    def ask_policy_question(payload: PolicyQuestionRequest) -> PolicyRequestDTO:
        return _execute_policy_question(payload.question, top_k=payload.top_k)

    @app.get("/api/v1/conversations", response_model=list[ConversationDTO])
    def list_conversations() -> list[ConversationDTO]:
        return [
            ConversationDTO(
                conversation_id=str(row["id"]),
                title=str(row["title"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                messages=[],
            )
            for row in _request_repository().list(CONVERSATIONS)
        ]

    @app.post("/api/v1/conversations", response_model=ConversationDTO, status_code=201)
    def create_conversation(payload: ConversationCreateRequest) -> ConversationDTO:
        conversation_id = f"CONV-{uuid4()}"
        now = datetime.now(timezone.utc)
        title = (payload.title or "新的制度问答").strip() or "新的制度问答"
        _request_repository().save(CONVERSATIONS, {
            "id": conversation_id,
            "title": title,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        })
        return ConversationDTO(
            conversation_id=conversation_id,
            title=title,
            created_at=now,
            updated_at=now,
        )

    @app.get("/api/v1/conversations/{conversation_id}", response_model=ConversationDTO)
    def get_conversation(conversation_id: str) -> ConversationDTO:
        return _conversation(conversation_id)

    @app.post(
        "/api/v1/conversations/{conversation_id}/messages",
        response_model=ConversationReplyDTO,
        status_code=201,
    )
    def send_conversation_message(
        conversation_id: str, payload: ConversationMessageRequest
    ) -> ConversationReplyDTO:
        conversation = _conversation(conversation_id)
        previous_user = next(
            (
                message.standalone_question or message.content
                for message in reversed(conversation.messages)
                if message.role == "user"
            ),
            None,
        )
        standalone = _standalone_question(payload.content, previous_user)
        policy_reply = _execute_policy_question(
            standalone,
            original_question=payload.content,
        )
        now = datetime.now(timezone.utc)
        user_message = ConversationMessageDTO(
            message_id=f"MSG-{uuid4()}",
            conversation_id=conversation_id,
            role="user",
            content=payload.content,
            created_at=now,
            standalone_question=standalone,
        )
        assistant_message = ConversationMessageDTO(
            message_id=f"MSG-{uuid4()}",
            conversation_id=conversation_id,
            role="assistant",
            content=policy_reply.result.summary,
            created_at=datetime.now(timezone.utc),
            standalone_question=standalone,
            result=policy_reply.result,
            review_id=policy_reply.review_id,
        )
        for message in (user_message, assistant_message):
            _request_repository().save(
                CONVERSATION_MESSAGES,
                {"id": message.message_id, **message.model_dump(mode="json")},
            )
        updated = datetime.now(timezone.utc)
        title = conversation.title
        if not conversation.messages and title == "新的制度问答":
            title = payload.content[:30]
        _request_repository().save(CONVERSATIONS, {
            "id": conversation_id,
            "title": title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": updated.isoformat(),
        })
        return ConversationReplyDTO(
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_message=assistant_message,
        )

    @app.get("/api/v1/policy/requests/{request_id}", response_model=PolicyRequestDTO)
    def get_policy_request(request_id: str) -> PolicyRequestDTO:
        rows = _request_repository().list(POLICY_REQUESTS)
        row = next((item for item in rows if item.get("id") == request_id), None)
        if row is None:
            raise HTTPException(status_code=404, detail="查询记录不存在")
        return PolicyRequestDTO.model_validate(
            {key: value for key, value in row.items() if key in {"question", "result", "review_id"}}
        )

    @app.post("/api/v1/invoice-audits", response_model=AgentResultDTO, status_code=201)
    def audit_invoice(payload: InvoiceAuditRequest) -> AgentResultDTO:
        result = _agent_result(build_invoice_audit_service().audit_invoice(payload.model_dump()))
        _request_repository().save(
            INVOICE_AUDITS,
            {"id": result.request_id, "result": result.model_dump(mode="json")},
        )
        return result

    @app.get("/api/v1/invoice-audits/{request_id}", response_model=AgentResultDTO)
    def get_invoice_audit(request_id: str) -> AgentResultDTO:
        row = next(
            (item for item in _request_repository().list(INVOICE_AUDITS) if item.get("id") == request_id),
            None,
        )
        if row is None:
            raise HTTPException(status_code=404, detail=f"审核记录不存在：{request_id}")
        return AgentResultDTO.model_validate(row["result"])

    @app.get("/api/v1/reviews", response_model=list[ReviewSummaryDTO])
    def list_reviews(status: str = "pending") -> list[ReviewSummaryDTO]:
        service = build_evaluation_service()
        records = service.list_pending_human_reviews() if status == "pending" else service.list_tests()
        return [_review_summary(record) for record in records]

    @app.get("/api/v1/reviews/{review_id}", response_model=ReviewDetailDTO)
    def review_detail(review_id: str) -> ReviewDetailDTO:
        service = build_evaluation_service()
        record = next((item for item in service.list_tests() if item.test_id == review_id), None)
        if record is None:
            raise HTTPException(status_code=404, detail="复核任务不存在")
        summary = _review_summary(record)
        decisions = [
            review.model_dump(mode="json")
            for review in service.list_reviews()
            if review.test_id == review_id
        ]
        return ReviewDetailDTO(
            **summary.model_dump(),
            input_sample=record.input_sample,
            findings=list(record.agent_output.get("findings", [])),
            sources=list(record.agent_output.get("sources", [])),
            agent_output=record.agent_output,
            decisions=decisions,
        )

    @app.post("/api/v1/reviews/{review_id}/decisions", status_code=201)
    def decide_review(review_id: str, payload: ReviewDecisionRequest) -> dict[str, object]:
        record = build_evaluation_service().submit_review(
            test_id=review_id,
            reviewer=payload.reviewer,
            review_decision=payload.decision,
            notes=payload.notes,
            overridden_recommendation=payload.overridden_recommendation,
        )
        return record.model_dump(mode="json")

    @app.get("/api/v1/metrics/summary", response_model=MetricsSummaryDTO)
    def metrics_summary() -> MetricsSummaryDTO:
        service = build_evaluation_service()
        tests = service.list_tests()
        reviews = service.list_reviews()
        failures = service.list_failures()
        gate = build_pilot_gate_service().evaluate(tests, failures, reviews)
        passed = sum(record.outcome == TestOutcome.PASS for record in tests)
        return MetricsSummaryDTO(
            total_tests=len(tests),
            passed_tests=passed,
            overall_pass_rate=passed / len(tests) if tests else 0,
            pending_reviews=len(service.list_pending_human_reviews()),
            completed_reviews=len([record for record in reviews if not record.is_simulated_review]),
            open_failures=len([record for record in failures if record.fix_status != "fixed"]),
            modules=[module.model_dump(mode="json") for module in gate.modules],
        )

    @app.get("/api/v1/pilot-gate")
    def pilot_gate() -> dict[str, object]:
        service = build_evaluation_service()
        return build_pilot_gate_service().evaluate(
            service.list_tests(), service.list_failures(), service.list_reviews()
        ).model_dump(mode="json")

    return app


app = create_app()
