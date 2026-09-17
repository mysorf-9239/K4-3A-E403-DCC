"""Nhắc hạn nộp **tự đăng ký** (opt-in) cho học viên.

Thiết kế theo câu hỏi của đề B2 "chủ động đến đâu thì thành phiền": bot không bao giờ nhắc người chưa bật. Mỗi đăng
ký gồm người dùng, hạng mục và số phút nhắc trước hạn; tắt bằng ``/remind-off``.

Hạn lấy từ ``registry.upcoming_deadlines`` (mục đang hiệu lực, có mốc tuyệt đối hoặc hạn lặp mỗi ngày, đã bỏ mốc bị
ghi đè). Mỗi cặp (người dùng, mục nguồn, mốc hạn) chỉ nhắc một lần.

Dữ liệu: ``data/runtime/reminders.json`` = ``{"subs": [...], "sent": [...]}`` (không commit).
"""
from datetime import datetime
from typing import Any

from . import config, registry
from .storage import locked, read_json, write_json

REMINDER_FILE = config.RUNTIME_DIR / "reminders.json"
MAX_SENT_KEYS = 2000


def _load() -> dict[str, list[Any]]:
    """Đọc dữ liệu nhắc hạn."""
    return read_json(REMINDER_FILE, {"subs": [], "sent": []})


def _save(data: dict[str, list[Any]]) -> None:
    """Ghi dữ liệu nhắc hạn, chỉ giữ ``MAX_SENT_KEYS`` khoá đã gửi gần nhất."""
    data["sent"] = data["sent"][-MAX_SENT_KEYS:]
    write_json(REMINDER_FILE, data)


def subscribe(user_id: int | str, item: str, lead_minutes: int = 120) -> dict[str, Any]:
    """Bật (hoặc cập nhật) nhắc hạn cho một hạng mục; trả đăng ký đã lưu."""
    sub = {"user_id": str(user_id), "item": item, "lead_minutes": int(lead_minutes),
           "created": config.now().strftime("%Y-%m-%d %H:%M")}
    with locked(REMINDER_FILE):
        data = _load()
        data["subs"] = [s for s in data["subs"] if not (s["user_id"] == sub["user_id"] and s["item"] == item)]
        data["subs"].append(sub)
        _save(data)
    return sub


def unsubscribe(user_id: int | str, item: str | None = None) -> int:
    """Tắt nhắc hạn một hạng mục, hoặc tất cả nếu ``item`` là ``None``; trả số đăng ký đã xoá."""
    with locked(REMINDER_FILE):
        data = _load()
        before = len(data["subs"])
        data["subs"] = [s for s in data["subs"]
                        if not (s["user_id"] == str(user_id) and (item is None or s["item"] == item))]
        _save(data)
    return before - len(data["subs"])


def list_subs(user_id: int | str) -> list[dict[str, Any]]:
    """Các đăng ký của một người dùng."""
    return [s for s in _load()["subs"] if s["user_id"] == str(user_id)]


def due_notifications(now: datetime | None = None) -> list[dict[str, Any]]:
    """Tính các lời nhắc cần gửi ngay và đánh dấu đã gửi.

    Args:
        now: Thời điểm tính (mặc định ``config.now()``).

    Returns:
        ``{"user_id", "item", "deadline", "minutes_left"}`` với ``deadline`` là một phần tử của
        ``registry.upcoming_deadlines``.
    """
    now = now or config.now()
    out = []
    with locked(REMINDER_FILE):
        data = _load()
        sent = set(data["sent"])
        for sub in data["subs"]:
            for deadline in registry.upcoming_deadlines(now, hours=sub["lead_minutes"] / 60, item=sub["item"]):
                key = f"{sub['user_id']}|{deadline['entry_id']}|{deadline['due_at']:%Y-%m-%dT%H:%M}"
                if key in sent:
                    continue
                sent.add(key)
                data["sent"].append(key)
                out.append({"user_id": sub["user_id"], "item": sub["item"], "deadline": deadline,
                            "minutes_left": int((deadline["due_at"] - now).total_seconds() // 60)})
        if out:
            _save(data)
    return out
