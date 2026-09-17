"""Hàng chờ TA (gap queue) và log phản hồi của học viên.

Mỗi câu hỏi ``NOT_FOUND`` hoặc ``CONFLICT`` được gom vào một **cụm** (gap) để TA trả lời một lần cho mọi người hỏi
cùng ý. Khi TA duyệt, câu trả lời thành mục nguồn ``TA-xx`` (xem ``registry.add_ta_entry``) và người hỏi sau nhận
được câu trả lời có nguồn.

Luật gom cụm (chỉ so các cụm đang mở, cùng ``decision``, ``item`` và ``lab``):
    * ``CONFLICT`` cùng bộ ``source_ids`` → cùng cụm.
    * ``NOT_FOUND``: chủ đề LLM trả (``topic``) giống ≥ 0.6, hoặc câu hỏi giống một câu trong cụm ≥ 0.7
      (``difflib.SequenceMatcher``).

Dữ liệu: ``data/runtime/gaps.json``, ``data/runtime/feedback.jsonl`` (không commit, không lưu tên/ID người hỏi).
"""
from difflib import SequenceMatcher
from typing import Any

from . import config
from .storage import append_jsonl, locked, read_json, write_json

Gap = dict[str, Any]

GAP_FILE = config.RUNTIME_DIR / "gaps.json"
FEEDBACK_FILE = config.RUNTIME_DIR / "feedback.jsonl"
TOPIC_SIMILARITY = 0.6
QUESTION_SIMILARITY = 0.7


def _stamp() -> str:
    """Thời điểm hiện tại dạng ``YYYY-MM-DD HH:MM`` (giờ VN)."""
    return config.now().strftime("%Y-%m-%d %H:%M")


def list_gaps(status: str | None = "open") -> list[Gap]:
    """Liệt kê cụm theo trạng thái ``open`` | ``resolved`` | ``None`` (tất cả)."""
    return [g for g in read_json(GAP_FILE, []) if status is None or g["status"] == status]


def get(gap_id: str) -> Gap | None:
    """Lấy một cụm theo mã ``GAP-xxx``; ``None`` nếu không có."""
    return next((g for g in read_json(GAP_FILE, []) if g["id"] == gap_id), None)


def _similar(a: str | None, b: str | None) -> float:
    """Độ giống nhau 0..1 giữa hai chuỗi (không phân biệt hoa thường)."""
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()


def _same_cluster(gap: Gap, question: str, decision: dict[str, Any]) -> bool:
    """Câu hỏi mới có thuộc cụm ``gap`` không (theo luật trong docstring module)."""
    if gap["status"] != "open" or gap["decision"] != decision["decision"]:
        return False
    if gap["item"] != decision.get("item") or gap["lab"] != decision.get("lab"):
        return False
    if decision["decision"] == "CONFLICT":
        return sorted(gap["source_ids"]) == sorted(decision["source_ids"])
    return (_similar(gap["topic"], decision.get("topic")) >= TOPIC_SIMILARITY
            or any(_similar(q, question) >= QUESTION_SIMILARITY for q in gap["questions"]))


def add(question: str, decision: dict[str, Any]) -> tuple[Gap, bool]:
    """Đưa một câu hỏi vào cụm phù hợp hoặc tạo cụm mới.

    Args:
        question: Câu hỏi nguyên văn của học viên.
        decision: Kết quả ``decide()`` có ``decision`` là ``NOT_FOUND`` hoặc ``CONFLICT``.

    Returns:
        Cụm sau khi cập nhật và ``True`` nếu là cụm mới.
    """
    with locked(GAP_FILE):
        gaps = read_json(GAP_FILE, [])
        for gap in gaps:
            if _same_cluster(gap, question, decision):
                if question not in gap["questions"]:
                    gap["questions"].append(question)
                gap.update(count=gap["count"] + 1, updated=_stamp())
                write_json(GAP_FILE, gaps)
                return gap, False
        gap = {"id": f"GAP-{len(gaps) + 1:03d}", "status": "open", "decision": decision["decision"],
               "item": decision.get("item"), "lab": decision.get("lab"), "topic": decision.get("topic", ""),
               "source_ids": decision.get("source_ids", []), "questions": [question], "count": 1,
               "created": _stamp(), "updated": _stamp(), "message_id": None}
        write_json(GAP_FILE, gaps + [gap])
    return gap, True


def _update(gap_id: str, **fields: Any) -> None:
    """Cập nhật các trường của một cụm, có khoá."""
    with locked(GAP_FILE):
        gaps = read_json(GAP_FILE, [])
        for gap in gaps:
            if gap["id"] == gap_id:
                gap.update(fields)
        write_json(GAP_FILE, gaps)


def set_message_id(gap_id: str, message_id: int) -> None:
    """Lưu ID tin nhắn Discord hiển thị cụm để lần sau sửa tin thay vì gửi tin mới."""
    _update(gap_id, message_id=message_id)


def resolve(gap_id: str, entry_id: str, ta_name: str) -> None:
    """Đánh dấu cụm đã được TA duyệt thành mục nguồn ``entry_id``."""
    _update(gap_id, status="resolved", resolved_by=ta_name, entry_id=entry_id, resolved_at=_stamp())


def log_feedback(trace_id: str, label: str, detail: str | None = None, channel: str = "unknown") -> None:
    """Ghi phản hồi của học viên cho một câu trả lời.

    Args:
        trace_id: Mã trace của lượt trả lời.
        label: ``thumbs_up`` | ``thumbs_down`` | ``wrong_item``.
        detail: Lý do chọn khi bấm 👎 (ví dụ "Sai hạn nộp").
        channel: ``discord`` | ``web``.
    """
    append_jsonl(FEEDBACK_FILE, {"ts": config.now().isoformat(timespec="seconds"), "trace_id": trace_id,
                                 "label": label, "detail": detail, "channel": channel})
