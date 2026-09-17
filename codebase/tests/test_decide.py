"""Test quyết định trung tâm với LLM giả: guard (lỗi B1, B5), cache, lỗi quota, trace."""
import json

from dcc import config, decide
from dcc.llm import QuotaExceeded


def guard(llm: dict, hint: dict | None = None, question: str = "") -> tuple[dict, list[str]]:
    """Gọi ``_guard`` ngắn gọn cho test."""
    return decide._guard(llm, hint, question)


def test_found_superseded_source_uses_latest() -> None:
    """LLM trỏ bản cũ TB-01 → trả TB-02 và cảnh báo thay thế."""
    final, guards = guard({"decision": "FOUND", "item": "daily_standup", "source_ids": ["TB-01"]})
    assert final["decision"] == "FOUND" and final["source_ids"] == ["TB-02"]
    assert final["superseded"] == ["TB-01"]
    assert guards == ["superseded_to_latest:TB-01->TB-02"]


def test_source_of_wrong_item_is_rejected() -> None:
    """Lỗi B1: hỏi daily standup mà LLM chọn nguồn lab → tìm lại theo đúng hạng mục."""
    final, guards = guard({"decision": "FOUND", "item": "daily_standup", "source_ids": ["TB-03"]})
    assert final["decision"] == "FOUND" and final["source_ids"] == ["TB-02"]
    assert guards[0].startswith("source_item_mismatch")


def test_hint_item_wins_over_llm_source() -> None:
    """Lỗi B1: học viên bấm chọn 'Đề tài' nhưng LLM đưa nguồn mentor duty → trả nguồn đề tài."""
    final, _ = guard({"decision": "FOUND", "item": "mentor_duty", "source_ids": ["TB-05"]}, {"item": "de_tai"})
    assert final["item"] == "de_tai" and final["source_ids"] == ["TB-04"]


def test_unknown_source_becomes_not_found() -> None:
    """Mã nguồn bịa → bị bỏ, không còn nguồn → NOT_FOUND, không hiển thị gì."""
    final, guards = guard({"decision": "FOUND", "item": "mentor_duty", "source_ids": ["XX-9"]})
    assert final["decision"] == "NOT_FOUND" and final["source_ids"] == []
    assert guards == ["drop_unknown_source:XX-9", "no_valid_source->NOT_FOUND"]


def test_unknown_source_without_item_match_is_not_found() -> None:
    """Không còn nguồn hợp lệ và không có hạng mục → NOT_FOUND."""
    final, _ = guard({"decision": "FOUND", "item": None, "source_ids": ["XX-9"]})
    assert final["decision"] == "NOT_FOUND" and final["source_ids"] == []


def test_lab_without_number_asks_again() -> None:
    """Bài lab mà không biết số → CLARIFY thiếu lab."""
    final, _ = guard({"decision": "FOUND", "item": "lab", "source_ids": ["TB-03"]})
    assert final["decision"] == "CLARIFY" and final["missing"] == "lab"


def test_conflict_forced_even_if_llm_says_found() -> None:
    """LLM bỏ sót mâu thuẫn Lab 3 → guard ép CONFLICT với cả hai nguồn."""
    final, guards = guard({"decision": "FOUND", "item": "lab", "lab": 3, "source_ids": ["TB-07"]})
    assert final["decision"] == "CONFLICT" and set(final["source_ids"]) == {"TB-03", "TB-07"}
    assert "conflict_detected->CONFLICT" in guards


def test_lab_outside_source_scope_is_not_found() -> None:
    """Lab 7 không nằm trong TB-03 (Lab 1–4)."""
    final, _ = guard({"decision": "FOUND", "item": "lab", "lab": 7, "source_ids": ["TB-03"]})
    assert final["decision"] == "NOT_FOUND"


def test_injection_not_found_is_not_queued() -> None:
    """Lỗi B5: tin injection bị LLM xếp NOT_FOUND → OUT_OF_SCOPE để không vào hàng chờ TA."""
    final, guards = guard({"decision": "NOT_FOUND", "injection_detected": True})
    assert final["decision"] == "OUT_OF_SCOPE"
    assert "injection_not_queued->OUT_OF_SCOPE" in guards


def test_decide_writes_trace_and_uses_cache(fake_llm) -> None:
    """Lượt 1 gọi LLM và ghi trace đủ prompt/raw; lượt 2 cùng câu dùng cache, không gọi LLM."""
    calls = fake_llm({"decision": "FOUND", "item": "daily_standup", "source_ids": ["TB-02"], "topic": "daily"})
    first = decide.decide("daily standup hạn khi nào?", channel="test")
    second = decide.decide("Daily standup hạn khi nào?", channel="test")
    assert first["decision"] == second["decision"] == "FOUND"
    assert len(calls) == 1 and second["cached"] is True
    rows = [json.loads(line) for line in (config.LOG_DIR / "decisions.jsonl").read_text().splitlines()]
    assert "raw_response" in rows[-2] and "user_prompt" in rows[-2]
    assert rows[-1]["cache_hit_of"] == first["trace_id"]


def test_decide_without_cache_calls_llm_each_time(fake_llm) -> None:
    """Eval tắt cache: mỗi lượt là một lời gọi thật."""
    calls = fake_llm({"decision": "CLARIFY", "item": None})
    decide.decide("hạn nộp bài?", use_cache=False)
    decide.decide("hạn nộp bài?", use_cache=False)
    assert len(calls) == 2


def test_quota_error_returns_error_decision(fake_llm) -> None:
    """Hết quota → ERROR kiểu quota, không ném lỗi ra ngoài, không cache."""
    fake_llm(QuotaExceeded("Gemini 429 PerDay"))
    result = decide.decide("lab 2 nộp ở đâu?")
    assert result["decision"] == "ERROR" and result["error_kind"] == "quota"
    assert decide._CACHE == {}


def test_invalid_json_returns_error(fake_llm, monkeypatch) -> None:
    """Phản hồi không phải JSON → ERROR kiểu llm."""
    monkeypatch.setattr("dcc.decide.complete", lambda s, u: ("xin chào", {}))
    assert decide.decide("abc", use_cache=False)["error_kind"] == "llm"
