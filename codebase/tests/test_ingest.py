"""Test nạp nguồn với LLM giả: kiểm tra quan hệ, trích dẫn, duyệt có sửa (lỗi B4), bỏ qua."""
import pytest

from dcc import ingest, registry


def extraction(**entry: object) -> dict:
    """Payload LLM giả với một mục trích xuất."""
    base = {"item": "daily_standup", "labs": None, "scope": "K4", "title": "Daily cập nhật", "who": "Mỗi người",
            "where": "Thread team", "how": "hôm hôm nay", "deadline": "07:00–22:00 mỗi ngày", "deadlines": [],
            "recurring_daily_close": "22:00", "consequence": "", "quote": "khung nộp daily đổi thành 07:00–22:00",
            "relation": "UPDATE", "related_ids": ["TB-02"], "reason": "cập nhật"}
    base.update(entry)
    return {"is_submission_notice": True, "injection_detected": False, "entries": [base]}


NOTICE = "[CẬP NHẬT] Từ 18/09 khung nộp daily đổi thành 07:00–22:00 mỗi ngày."


def test_update_proposal_then_edit_and_approve(fake_llm) -> None:
    """Đề xuất UPDATE được lưu; TA sửa lỗi chữ AI rồi duyệt → nguồn mới thay TB-02 và mang nội dung đã sửa."""
    fake_llm(extraction())
    result = ingest.propose(NOTICE, "#announcements", channel="test")
    proposal = result["proposals"][0]
    assert proposal["relation"] == "UPDATE" and proposal["status"] == "pending"
    entry = ingest.approve(proposal["id"], "TA", edits={"how": "Gõ /daily-standup"})
    assert entry["how"] == "Gõ /daily-standup" and entry["reviewed_edit"] is True
    assert registry.latest_version("TB-02")["id"] == entry["id"]
    assert ingest.get(proposal["id"])["edited"] is True


def test_new_but_existing_item_becomes_conflict(fake_llm) -> None:
    """LLM gọi NEW nhưng sổ đã có daily standup với hạn khác → CONFLICT."""
    fake_llm(extraction(relation="NEW", related_ids=[]))
    proposal = ingest.propose(NOTICE, "#a", channel="test")["proposals"][0]
    assert proposal["relation"] == "CONFLICT" and "TB-02" in proposal["related_ids"]


def test_same_deadline_detected_as_duplicate_and_cannot_be_approved(fake_llm) -> None:
    """Hạn trùng mục đã có → DUPLICATE; duyệt bị từ chối."""
    fake_llm(extraction(relation="NEW", related_ids=[], deadline="06:00–23:59 mỗi ngày (giờ VN), áp dụng từ 16/09"))
    proposal = ingest.propose(NOTICE, "#a", channel="test")["proposals"][0]
    assert proposal["relation"] == "DUPLICATE"
    with pytest.raises(ValueError):
        ingest.approve(proposal["id"], "TA")


def test_quote_must_be_verbatim(fake_llm) -> None:
    """Trích dẫn không có trong thông báo → thay bằng đầu thông báo và gắn guard."""
    fake_llm(extraction(quote="câu AI tự bịa"))
    proposal = ingest.propose(NOTICE, "#a", channel="test")["proposals"][0]
    assert "quote_not_verbatim" in proposal["guards"]
    assert proposal["entry"]["quote"] == NOTICE[:200]


def test_invalid_item_and_bad_due_at_are_dropped(fake_llm) -> None:
    """Hạng mục lạ bị bỏ; mốc giờ sai định dạng bị bỏ kèm guard."""
    fake_llm({"is_submission_notice": True, "entries": [
        extraction()["entries"][0] | {"item": "thu_vien"},
        extraction(item="lab", labs=[5], relation="NEW", related_ids=[], recurring_daily_close=None,
                   deadlines=[{"label": "Lab 5", "due_at": "thứ Sáu"}])["entries"][0]]})
    result = ingest.propose("Lab 5 nộp trước thứ Sáu", "#a", channel="test")
    assert "invalid_item:thu_vien" in result["guards"]
    assert len(result["proposals"]) == 1 and "bad_due_at:thứ Sáu" in result["proposals"][0]["guards"]


def test_bad_edited_deadlines_raise(fake_llm) -> None:
    """TA sửa mốc giờ sai định dạng → báo lỗi rõ, không ghi sổ."""
    fake_llm(extraction())
    proposal = ingest.propose(NOTICE, "#a", channel="test")["proposals"][0]
    with pytest.raises(ValueError, match="sai định dạng"):
        ingest.approve(proposal["id"], "TA", edits={"deadlines": "CP3 17/9"})
    assert ingest.get(proposal["id"])["status"] == "pending"


def test_reject_and_eval_channel_not_stored(fake_llm) -> None:
    """Bỏ qua đổi trạng thái; đề xuất từ eval không được lưu vào hàng chờ."""
    fake_llm(extraction())
    proposal = ingest.propose(NOTICE, "#a", channel="test")["proposals"][0]
    ingest.reject(proposal["id"], "TA")
    assert ingest.get(proposal["id"])["status"] == "rejected"
    eval_result = ingest.propose(NOTICE, "#a", channel="eval:I02")
    assert eval_result["proposals"][0]["id"] == "EVAL-1"
    assert len(ingest.list_proposals(None)) == 1


def test_parse_deadlines_text_roundtrip() -> None:
    """Văn bản mốc giờ TA sửa đọc/ghi ngược nhau."""
    items = [{"label": "CP3 · Video", "due_at": "2026-09-17T16:00"}]
    assert ingest.parse_deadlines_text(ingest.deadlines_to_text(items)) == items


def test_normalize_due_accepts_space_and_seconds() -> None:
    """LLM trả '2026-09-17 18:00' (dấu cách) vẫn được giữ — lỗi thật gặp ở eval I08 lượt 3."""
    assert ingest.normalize_due("2026-09-17 18:00") == "2026-09-17T18:00"
    assert ingest.normalize_due("2026-09-17T18:00:00") == "2026-09-17T18:00"
    assert ingest.normalize_due("thứ Sáu") is None
    assert ingest.normalize_due("2026-13-40 18:00") is None
