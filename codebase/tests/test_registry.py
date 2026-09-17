"""Test sổ nguồn: phiên bản, mâu thuẫn, thay thế toàn bộ / theo lab / theo mốc (lỗi B3), hạn sắp tới."""
from datetime import datetime

from dcc import registry

CONTENT = {"where": "VLearn", "how": "Nộp link repo", "deadline": "12:00 hôm sau", "who": ""}


def test_superseded_entry_resolves_to_latest() -> None:
    """TB-01 đã bị TB-02 thay thế."""
    assert registry.latest_version("TB-01")["id"] == "TB-02"


def test_lab3_sources_conflict() -> None:
    """TB-03 (Lab 1–4) và TB-07 (Lab 3) khác hạn, không liên kết → mâu thuẫn."""
    index = registry.by_id()
    assert registry.find_conflicts(index["TB-07"], index) == ["TB-03"]


def test_ta_answer_for_one_lab_does_not_break_other_labs() -> None:
    """Giải quyết mâu thuẫn Lab 3 chỉ ghi đè Lab 3; Lab 2 vẫn dùng TB-03 và TB-07 bị thay thế."""
    entry = registry.add_ta_entry("lab", CONTENT, "TA", "Lab 3 lớp 3A?", [3], ["TB-03", "TB-07"])
    index = registry.by_id()
    assert index["TB-03"]["status"] == "active"
    assert index["TB-07"]["status"] == "superseded"
    assert registry.override_for(index["TB-03"], 3, "", index)["id"] == entry["id"]
    assert registry.override_for(index["TB-03"], 2, "", index) is None
    assert registry.find_conflicts(index[entry["id"]], index) == []


def test_partial_checkpoint_update_keeps_other_deadlines() -> None:
    """Gia hạn riêng CP3 không xoá CP4/CP5 của TB-06 (lỗi B3)."""
    new = {"kind": "official", "origin": "ingested", "item": "hackathon_checkpoint", "title": "Gia hạn CP3",
           "who": "Đội trưởng", "where": "Form CP3", "how": "Video + số đo", "deadline": "CP3 18:00 17/9",
           "consequence": "", "quote": "CP3 gia hạn", "source": "#announcements", "published": "2026-09-17 09:00",
           "deadlines": [{"label": "CP3 · Video", "due_at": "2026-09-17T18:00"}]}
    saved = registry.add_entry(new, ["TB-06"])
    index = registry.by_id()
    assert index["TB-06"]["status"] == "active"
    assert saved["deadline_keys"] == ["CP3"]
    upcoming = registry.upcoming_deadlines(now=datetime(2026, 9, 17, 8, 0), hours=36, item="hackathon_checkpoint")
    labels = [(d["entry_id"], d["label"]) for d in upcoming]
    assert (saved["id"], "CP3 · Video") in labels
    assert not any(eid == "TB-06" and label.startswith("CP3") for eid, label in labels)
    assert any(label.startswith("CP4") for _, label in labels)
    assert registry.override_for(index["TB-06"], None, "hạn CP3 khi nào?", index)["id"] == saved["id"]


def test_full_update_supersedes_old_entry() -> None:
    """Cập nhật toàn bộ daily standup thay thế TB-02."""
    new = {"kind": "official", "origin": "ingested", "item": "daily_standup", "title": "Daily mới", "who": "Mỗi người",
           "where": "Thread", "how": "/daily-standup", "deadline": "07:00–22:00", "consequence": "", "quote": "q",
           "source": "#a", "published": "2026-09-17 08:00", "recurring_daily_close": "22:00"}
    saved = registry.add_entry(new, ["TB-02"])
    assert registry.latest_version("TB-01")["id"] == saved["id"]


def test_upcoming_deadlines_recurring_without_duplicates() -> None:
    """Hạn lặp mỗi ngày xuất hiện đúng một lần mỗi ngày trong cửa sổ."""
    items = registry.upcoming_deadlines(now=datetime(2026, 9, 17, 8, 0), hours=24, item="daily_standup")
    assert [d["due_at"] for d in items] == [datetime(2026, 9, 17, 23, 59)]


def test_fingerprint_changes_when_registry_changes() -> None:
    """Dấu vân tay đổi khi có mục mới (để cache câu trả lời tự hết hiệu lực)."""
    before = registry.fingerprint()
    registry.add_ta_entry("mentor_duty", CONTENT, "TA", "mentor?")
    assert registry.fingerprint() != before
