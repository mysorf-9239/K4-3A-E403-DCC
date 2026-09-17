"""Test API web với LLM giả: hỏi đáp, quyền TA (lỗi B6), duyệt đề xuất có sửa."""
from fastapi.testclient import TestClient

from web.app import app

client = TestClient(app)


def test_ask_found_returns_card_with_source(fake_llm) -> None:
    """Hỏi daily standup → thẻ FOUND có trích dẫn TB-02."""
    fake_llm({"decision": "FOUND", "item": "daily_standup", "source_ids": ["TB-02"]})
    body = client.post("/api/ask", json={"question": "daily standup hạn khi nào?"}).json()
    assert body["decision"]["decision"] == "FOUND"
    assert body["card"]["sources"][0]["line"].startswith("TB-02")
    assert body["gap"] is None


def test_ask_not_found_creates_gap(fake_llm) -> None:
    """NOT_FOUND → có cụm hàng chờ TA."""
    fake_llm({"decision": "NOT_FOUND", "item": "lab", "lab": 7, "topic": "lab 7"})
    body = client.post("/api/ask", json={"question": "Lab 7 nộp ở đâu?"}).json()
    assert body["gap"]["id"] == "GAP-001"


def test_empty_question_rejected() -> None:
    """Câu hỏi rỗng bị từ chối bởi validation."""
    assert client.post("/api/ask", json={"question": ""}).status_code == 422


def test_ta_endpoint_requires_token_when_configured(monkeypatch) -> None:
    """Có WEB_TA_TOKEN thì thiếu/sai token → 401, đúng token → 200."""
    monkeypatch.setenv("WEB_TA_TOKEN", "secret")
    assert client.get("/api/gaps").status_code == 401
    assert client.get("/api/gaps", headers={"X-TA-Token": "sai"}).status_code == 401
    assert client.get("/api/gaps", headers={"X-TA-Token": "secret"}).status_code == 200


def test_ta_endpoint_rejects_remote_host_without_token() -> None:
    """Không đặt token → chỉ máy chạy server được gọi thao tác TA."""
    remote = TestClient(app, client=("203.0.113.5", 5000))
    assert remote.get("/api/proposals").status_code == 403
    assert client.get("/api/proposals").status_code == 200


def test_approve_proposal_with_edits(fake_llm) -> None:
    """Nạp thông báo qua API rồi duyệt kèm nội dung sửa."""
    fake_llm({"is_submission_notice": True, "entries": [{
        "item": "lab", "labs": [5], "title": "Lab 5", "who": "Từng học viên", "where": "VLearn", "how": "link repo",
        "deadline": "23:59 19/09", "deadlines": [{"label": "Lab 5", "due_at": "2026-09-19T23:59"}],
        "quote": "Lab 5 nộp trên VLearn", "relation": "NEW", "related_ids": []}]})
    result = client.post("/api/ingest", json={"text": "Lab 5 nộp trên VLearn trước 23:59 19/09"}).json()
    pid = result["proposals"][0]["id"]
    entry = client.post(f"/api/proposals/{pid}/approve",
                        json={"edits": {"where": "VLearn → Lab 5"}}).json()["entry"]
    assert entry["id"] == "SRC-01" and entry["where"] == "VLearn → Lab 5"
