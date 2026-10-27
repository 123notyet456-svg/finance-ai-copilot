from pathlib import Path

from fastapi.testclient import TestClient

from finance_copilot.interfaces.api.app import create_app


def test_policy_question_and_review_contract(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FINANCE_COPILOT_DATABASE", str(tmp_path / "records.db"))
    monkeypatch.setenv("FINANCE_COPILOT_VECTOR_DB", str(tmp_path / "vectors.db"))
    client = TestClient(create_app())

    context = client.get("/api/v1/context")
    assert context.status_code == 200
    assert context.json()["authentication_mode"] == "demo_role_switch"

    answer = client.post(
        "/api/v1/policy/questions",
        json={"question": "上海出差住宿标准是什么？", "top_k": 5},
    )
    assert answer.status_code == 201
    body = answer.json()
    assert body["result"]["execution_status"] == "completed"
    assert body["result"]["recommendation"] in {
        "pass", "warning", "needs_review", "reject"
    }
    assert "sources" in body["result"]

    stored = client.get(f"/api/v1/policy/requests/{body['result']['request_id']}")
    assert stored.status_code == 200
    assert stored.json()["question"] == "上海出差住宿标准是什么？"


def test_invoice_metrics_and_openapi_contract(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FINANCE_COPILOT_DATABASE", str(tmp_path / "records.db"))
    client = TestClient(create_app())
    invoice = client.post(
        "/api/v1/invoice-audits",
        json={
            "invoice_number": "SYNTHETIC-API-001",
            "invoice_date": "2026-06-30",
            "buyer_name": "虚构科技有限公司",
            "seller_name": "合成服务有限公司",
            "amount": "100.00",
            "tax": "6.00",
            "total_amount": "106.00",
        },
    )
    assert invoice.status_code == 201
    assert invoice.json()["module"] == "invoice_audit"
    stored = client.get(f"/api/v1/invoice-audits/{invoice.json()['request_id']}")
    assert stored.status_code == 200
    assert client.get("/api/v1/metrics/summary").status_code == 200

    schema = client.get("/openapi.json").json()
    assert "/api/v1/reviews/{review_id}/decisions" in schema["paths"]


def test_error_contract(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FINANCE_COPILOT_DATABASE", str(tmp_path / "records.db"))
    client = TestClient(create_app())
    response = client.get("/api/v1/policy/requests/missing")
    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"
    assert response.json()["request_id"]


def test_upload_document_and_toggle_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FINANCE_COPILOT_DATABASE", str(tmp_path / "records.db"))
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/policy/documents/upload",
        files={"file": ("external-policy.md", "# 外部采购制度\n采购申请超过 5000 元需部门负责人审批。".encode(), "text/markdown")},
        data={"title": "外部采购制度", "version": "2026.1"},
    )
    assert response.status_code == 201
    document = response.json()
    assert document["source"] == "upload"
    assert document["content_hash"]
    assert document["chunk_count"] == 1

    disabled = client.patch(
        f"/api/v1/policy/documents/{document['document_id']}",
        json={"processing_status": "disabled"},
    )
    assert disabled.status_code == 200
    assert disabled.json()["processing_status"] == "disabled"


def test_multi_turn_conversation_resolves_city_follow_up(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FINANCE_COPILOT_DATABASE", str(tmp_path / "records.db"))
    monkeypatch.setenv("FINANCE_COPILOT_VECTOR_DB", str(tmp_path / "vectors.db"))
    client = TestClient(create_app())
    created = client.post("/api/v1/conversations", json={}).json()
    conversation_id = created["conversation_id"]

    first = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "上海出差住宿标准是什么？"},
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "那北京呢？"},
    )
    assert second.status_code == 201
    standalone = second.json()["user_message"]["standalone_question"]
    assert "北京" in standalone
    assert "上海" not in standalone

    third = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "那需要哪些材料？"},
    )
    assert third.status_code == 201
    third_standalone = third.json()["user_message"]["standalone_question"]
    assert "北京" in third_standalone
    assert "住宿标准" in third_standalone

    stored = client.get(f"/api/v1/conversations/{conversation_id}")
    assert stored.status_code == 200
    assert [message["role"] for message in stored.json()["messages"]] == [
        "user", "assistant", "user", "assistant", "user", "assistant"
    ]
