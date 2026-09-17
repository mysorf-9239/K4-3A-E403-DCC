"""Test hàng chờ TA, nhắc hạn, bản tin, giới hạn tốc độ LLM (lỗi B9) và khoá ghi file (lỗi B7)."""
import json
import threading
from datetime import datetime

from dcc import config, digest, gaps, llm, reminders, storage


def test_gap_clustering_by_similar_question() -> None:
    """Hai cách hỏi giống nhau về Lab 7 vào cùng cụm; mâu thuẫn khác thì cụm riêng."""
    d = {"decision": "NOT_FOUND", "item": "lab", "lab": 7, "topic": "nop lab 7", "source_ids": []}
    first, new1 = gaps.add("Lab 7 nộp ở đâu?", d)
    second, new2 = gaps.add("lab 7 nộp ở đâu vậy", d | {"topic": "noi nop lab 7"})
    conflict, new3 = gaps.add("Lab 3 3A?", {"decision": "CONFLICT", "item": "lab", "lab": 3, "topic": "x",
                                            "source_ids": ["TB-03", "TB-07"]})
    assert new1 and not new2 and new3
    assert second["id"] == first["id"] and second["count"] == 2
    assert conflict["id"] != first["id"]


def test_reminder_sent_once_per_deadline() -> None:
    """Nhắc CP3 khi còn trong khoảng 120 phút, chỉ một lần."""
    reminders.subscribe(1, "hackathon_checkpoint", 120)
    first = reminders.due_notifications(now=datetime(2026, 9, 17, 14, 30))
    again = reminders.due_notifications(now=datetime(2026, 9, 17, 14, 45))
    assert [n["deadline"]["label"] for n in first] == ["CP3 · Video 30s + số đo"]
    assert again == []
    assert reminders.unsubscribe(1) == 1


def test_digest_counts_from_logs() -> None:
    """Bản tin đếm quyết định từ log (bỏ lượt eval) và cụm đang mở."""
    now = datetime(2026, 9, 17, 12, 0)
    rows = [{"ts": "2026-09-17T10:00:00", "channel": "discord", "final": {"decision": "FOUND"}},
            {"ts": "2026-09-17T10:05:00", "channel": "eval:C01", "final": {"decision": "FOUND"}}]
    (config.LOG_DIR / "decisions.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    gaps.add("Lab 7?", {"decision": "NOT_FOUND", "item": "lab", "lab": 7, "topic": "lab 7", "source_ids": []})
    data = digest.build(hours=24, now=now)
    assert data["asked"] == 1 and data["decisions"]["FOUND"] == 1 and data["open_gap_total"] == 1
    assert "Bản tin DCC cho TA" in digest.to_markdown(data)


def test_rate_limiter_waits_when_over_limit(monkeypatch) -> None:
    """Quá ngưỡng request/phút thì chờ thay vì gọi ngay."""
    clock = {"t": 0.0}
    monkeypatch.setattr(llm.time, "monotonic", lambda: clock["t"])
    monkeypatch.setattr(llm.time, "sleep", lambda s: clock.__setitem__("t", clock["t"] + s))
    limiter = llm.RateLimiter(2)
    assert limiter.acquire() == 0 and limiter.acquire() == 0
    assert limiter.acquire() > 59


def test_retry_delay_uses_provider_hint() -> None:
    """Chờ theo "retry in Xs" của provider; hết quota ngày không thử lại."""
    assert llm._retry_delay(Exception("Please retry in 14.5s"), 1) == 15.5
    assert llm._retry_delay(Exception("boom"), 3) == 6.0
    assert llm._transient(llm.LLMError("Gemini 503: busy"))
    assert not llm._transient(llm.QuotaExceeded("Gemini 429 PerDay"))


def test_locked_writes_do_not_lose_updates() -> None:
    """Nhiều luồng cùng đọc-sửa-ghi qua ``locked`` không làm mất lượt cập nhật."""
    path = config.RUNTIME_DIR / "counter.json"
    storage.write_json(path, {"n": 0})

    def bump() -> None:
        """Tăng bộ đếm 50 lần qua khoá file."""
        for _ in range(50):
            with storage.locked(path):
                data = storage.read_json(path, {"n": 0})
                data["n"] += 1
                storage.write_json(path, data)

    threads = [threading.Thread(target=bump) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert storage.read_json(path, {})["n"] == 200
