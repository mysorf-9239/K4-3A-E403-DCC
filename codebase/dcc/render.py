"""Chuyển quyết định thành "thẻ trả lời" trung lập về giao diện, dùng chung cho Discord và web.

Thẻ (card) là dict:
    decision: mã quyết định; color: màu 0xRRGGBB; label: nhãn ngắn có emoji.
    title, description: tiêu đề và mô tả (có thể rỗng; mô tả dùng ``**đậm**`` kiểu Markdown).
    fields: list ``(tên, giá trị)`` — nội dung lấy nguyên văn từ sổ nguồn.
    sources: list ``{"line": "TB-02 · … · ngày", "quote": "trích dẫn"}``.
    warning, note: cảnh báo / ghi chú phụ, có thể ``None``.
    actions: nút cần hiển thị — ``wrong_item``, ``thumbs_up``, ``pick_item``, ``pick_lab``, ``ask_ta_manual``.
    trace_id: mã trace để gắn phản hồi.
"""
from typing import Any

from . import config, registry

Card = dict[str, Any]

COLORS = {"FOUND": 0x1F9D6B, "CONFLICT": 0xE0A100, "CLARIFY": 0x3B82F6,
          "NOT_FOUND": 0xC9443B, "OUT_OF_SCOPE": 0x6A4FC4, "ERROR": 0x6B7280}

LABELS = {"FOUND": "✅ Có nguồn chính thức", "CONFLICT": "⚠️ Các nguồn đang mâu thuẫn",
          "CLARIFY": "❓ Cần bạn nói rõ hơn", "NOT_FOUND": "🔎 Chưa có nguồn chính thức",
          "OUT_OF_SCOPE": "🚫 Ngoài phạm vi của DCC", "ERROR": "⚙️ DCC đang gặp lỗi"}

ORIGIN_LABELS = {"public_doc": "Tài liệu công khai của khoá", "simulated": "Thông báo giả lập (demo)",
                 "ingested": "Thông báo đã nạp, TA duyệt", "ta": "TA xác nhận"}


def item_label(item: str | None, lab: int | None = None) -> str:
    """Nhãn hạng mục cho người đọc, ví dụ ``("lab", 3)`` → "Bài lab 3"."""
    if not item:
        return "yêu cầu nộp bài"
    return config.ITEMS.get(item, item) + (f" {lab}" if lab else "")


def source_line(entry: registry.Entry) -> str:
    """Dòng mô tả nguồn: mã · loại nguồn · kênh/tài liệu · thời điểm đăng (· link nếu có)."""
    kind = ORIGIN_LABELS.get(entry.get("origin", ""), "Thông báo chính thức")
    line = f"{entry['id']} · {kind} · {entry['source']} · {entry['published']}"
    return f"{line} · {entry['url']}" if entry.get("url") else line


def _found(c: Card, d: dict[str, Any], index: dict[str, registry.Entry]) -> None:
    """Điền thẻ FOUND: 5 trường từ nguồn, trích dẫn, cảnh báo bản cũ / mốc đã được cập nhật."""
    e = index[d["source_ids"][0]]
    c["title"] = e["title"]
    c["fields"] = [("Ai nộp", e["who"]), ("Nơi nộp", e["where"]), ("Cách nộp", e["how"]),
                   ("Hạn nộp", e["deadline"]), ("Lưu ý", e["consequence"])]
    c["sources"] = [{"line": source_line(e), "quote": e["quote"]}]
    warnings = []
    if d.get("superseded"):
        warnings.append(f"Thông báo này thay thế {', '.join(d['superseded'])}; quy định khác bạn từng nghe là bản cũ.")
    updates = registry.partial_updates(e, index)
    if updates:
        parts = ", ".join(f"{u['id']} ({', '.join(u.get('deadline_keys') or map(str, u.get('labs') or []))})"
                          for u in updates)
        warnings.append(f"Một phần nội dung đã được cập nhật bởi {parts} — hỏi đúng mốc/lab để xem bản mới.")
    c["warning"] = " ".join(warnings) or None
    c["actions"] = ["wrong_item", "thumbs_up"]


def _conflict(c: Card, d: dict[str, Any], index: dict[str, registry.Entry]) -> None:
    """Điền thẻ CONFLICT: liệt kê mọi nguồn đang hiệu lực, không tự chọn."""
    entries = [index[s] for s in d["source_ids"]]
    c["title"] = f"{item_label(d['item'], d['lab'])}: có {len(entries)} thông báo nói khác nhau"
    c["description"] = ("DCC không tự chọn một bên vì chọn sai có thể làm bạn nộp muộn. "
                        "Các nguồn đang hiệu lực ở dưới; câu hỏi đã được gửi TA xác nhận.")
    for e in entries:
        c["fields"].append((f"{e['id']} — {e['scope']}", f"Hạn: {e['deadline']}"))
        c["sources"].append({"line": source_line(e), "quote": e["quote"]})
    latest = max(entries, key=lambda e: e["published"])
    c["warning"] = ("Trong lúc chờ TA: an toàn nhất là nộp trước mốc sớm hơn. "
                    f"Thông báo đăng gần nhất là {latest['id']} ({latest['published']}).")
    c["actions"] = ["wrong_item"]


def _no_source(c: Card, d: dict[str, Any]) -> None:
    """Điền thẻ CLARIFY / NOT_FOUND / OUT_OF_SCOPE / ERROR."""
    dec = d["decision"]
    if dec == "CLARIFY" and d.get("missing") == "lab":
        c["description"], c["actions"] = "Bạn hỏi **lab số mấy**? Mỗi lab có thể có hạn khác nhau.", ["pick_lab"]
    elif dec == "CLARIFY":
        c["description"] = "Bạn hỏi về **hạng mục nào**? Mỗi hạng mục có nơi nộp và hạn khác nhau, DCC không muốn đoán."
        c["actions"] = ["pick_item"]
    elif dec == "NOT_FOUND":
        c["description"] = (f"DCC **chưa tìm thấy thông báo chính thức** trả lời câu này về "
                            f"**{item_label(d['item'], d['lab'])}**, nên không đưa ra hạn hay nơi nộp để tránh bạn "
                            "nộp sai. Câu hỏi đã được gửi TA; khi TA xác nhận, lần hỏi sau sẽ có nguồn.")
        c["actions"] = ["wrong_item"]
    elif dec == "OUT_OF_SCOPE":
        c["description"] = ("DCC chỉ tra **nơi nộp · cách nộp · hạn nộp** theo thông báo chính thức. DCC không gia "
                            "hạn, không nộp hộ, không xem điểm/điểm danh cá nhân và không giải bài.")
        c["actions"] = ["ask_ta_manual", "wrong_item"]
    elif d.get("error_kind") == "quota":
        c["description"] = "Model AI đã hết quota trong ngày. Bạn thử lại sau hoặc hỏi trực tiếp TA."
    else:
        c["description"] = "DCC không gọi được AI lúc này. Bạn thử lại sau ít phút hoặc hỏi trực tiếp TA."


def card(d: dict[str, Any]) -> Card:
    """Dựng thẻ trả lời từ kết quả ``decide()``.

    Args:
        d: Dict quyết định (có ``decision``, ``source_ids``, ``item``, ``lab``…).

    Returns:
        Thẻ như mô tả ở docstring module.
    """
    index = registry.by_id()
    dec = d["decision"]
    c: Card = {"decision": dec, "color": COLORS[dec], "label": LABELS[dec], "title": "", "description": "",
               "fields": [], "sources": [], "warning": None, "note": d.get("note"),
               "actions": [], "trace_id": d.get("trace_id")}
    if dec == "FOUND":
        _found(c, d, index)
    elif dec == "CONFLICT":
        _conflict(c, d, index)
    else:
        _no_source(c, d)
    if d.get("injection_detected"):
        extra = "Tin nhắn có yêu cầu đổi quy tắc/đổi vai — DCC đã bỏ qua phần đó."
        c["note"] = f"{c['note']} · {extra}" if c["note"] else extra
    return c


def to_text(c: Card) -> str:
    """Chuyển thẻ thành văn bản Markdown thuần (dùng khi log hoặc kênh không hỗ trợ embed)."""
    lines = [f"**{c['label']}**"]
    if c["title"]:
        lines.append(f"**{c['title']}**")
    if c["description"]:
        lines.append(c["description"])
    lines += [f"• **{k}:** {v}" for k, v in c["fields"]]
    lines += [f"> {s['quote']}\n> — {s['line']}" for s in c["sources"]]
    if c["warning"]:
        lines.append(f"⚠️ {c['warning']}")
    if c["note"]:
        lines.append(f"ℹ️ {c['note']}")
    return "\n".join(lines)
