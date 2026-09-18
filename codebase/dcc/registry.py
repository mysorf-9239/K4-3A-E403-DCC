"""Sổ nguồn (source registry): nơi duy nhất chứa sự thật về yêu cầu nộp bài.

Sổ nguồn gồm hai lớp:

1. ``data/registry.json`` — sổ gốc commit vào repo:
   ``origin="public_doc"`` trích từ tài liệu công khai của khoá (có ``url``);
   ``origin="simulated"`` thông báo giả lập nhóm tự soạn để mô phỏng tình huống thật.
2. ``data/runtime/entries.json`` + ``data/runtime/overrides.json`` — phát sinh khi chạy (không commit):
   mục nạp từ thông báo đã được TA duyệt (``origin="ingested"``), câu trả lời TA cho hàng chờ
   (``kind="ta_answer"``) và đánh dấu "bị thay thế".

Mỗi mục (entry) là một dict với các khoá chính:
    id: ``TB-xx`` (sổ gốc), ``SRC-xx`` (nạp từ thông báo), ``TA-xx`` (TA trả lời hàng chờ).
    kind: ``official`` | ``ta_answer``; origin: ``public_doc`` | ``simulated`` | ``ingested`` | ``ta``.
    item: hạng mục trong ``config.ITEMS``; labs: (tuỳ chọn) danh sách số lab áp dụng;
    classes: (tuỳ chọn) danh sách lớp áp dụng, ví dụ ``["3A"]`` — không khai nghĩa là mọi lớp.
    status: ``active`` | ``superseded``; supersedes / superseded_by: quan hệ phiên bản.
    overrides: (tuỳ chọn) mã các mục bị mục này ghi đè **một phần** — theo lab (``labs``) hoặc theo mốc
        (``deadline_keys``, ví dụ chỉ đổi CP3 trong lịch CP1–CP5).
    who, where, how, deadline, consequence, quote: nội dung hiển thị, **luôn lấy nguyên văn** khi trả lời.
    source, url, published: nguồn gốc để học viên tự kiểm tra.
    deadlines: (tuỳ chọn) ``[{"label", "due_at": "YYYY-MM-DDTHH:MM"}]``; recurring_daily_close: ``"HH:MM"``.

Quy ước "mâu thuẫn": hai mục ``active`` cùng hạng mục, phạm vi lab giao nhau, phạm vi lớp giao nhau, ``deadline``
khác nhau và không mục nào thay thế hay ghi đè mục nào.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Any

from . import config
from .storage import locked, read_json, write_json

Entry = dict[str, Any]

ENTRIES_FILE = config.RUNTIME_DIR / "entries.json"
OVERRIDE_FILE = config.RUNTIME_DIR / "overrides.json"


def load_entries() -> list[Entry]:
    """Tải toàn bộ sổ nguồn đã áp dụng đánh dấu runtime.

    Returns:
        Mục sổ gốc + mục runtime. Mục bị thay thế lúc chạy có ``status="superseded"`` và ``superseded_by``.
    """
    entries = read_json(config.REGISTRY_FILE, {"entries": []})["entries"] + read_json(ENTRIES_FILE, [])
    overrides = read_json(OVERRIDE_FILE, {})
    for entry in entries:
        if entry["id"] in overrides:
            entry["status"] = "superseded"
            entry["superseded_by"] = overrides[entry["id"]]
    return entries


def by_id() -> dict[str, Entry]:
    """Trả về ``{id: entry}`` của sổ nguồn hiện tại."""
    return {e["id"]: e for e in load_entries()}


def fingerprint() -> str:
    """Mã băm nội dung sổ nguồn hiện tại — đổi khi có mục mới/bị thay thế (dùng làm khoá cache)."""
    raw = json.dumps(load_entries(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def latest_version(entry_id: str, index: dict[str, Entry] | None = None) -> Entry | None:
    """Đi theo chuỗi ``superseded_by`` tới phiên bản đang hiệu lực; ``None`` nếu mã không tồn tại."""
    index = index or by_id()
    seen: set[str] = set()
    cur = index.get(entry_id)
    while cur and cur.get("status") == "superseded" and cur.get("superseded_by") and cur["id"] not in seen:
        seen.add(cur["id"])
        cur = index.get(cur["superseded_by"])
    return cur


def superseded_chain(entry: Entry, index: dict[str, Entry] | None = None) -> list[str]:
    """Mã các mục cũ đã bị ``entry`` trực tiếp thay thế (dùng cho cảnh báo "quy định cũ")."""
    index = index or by_id()
    return [e["id"] for e in index.values() if e.get("superseded_by") == entry["id"]]


def labs_overlap(a: Entry, b: Entry) -> bool:
    """Hai mục có phạm vi lab giao nhau không. Mục không khai ``labs`` coi như áp dụng mọi lab."""
    la, lb = a.get("labs"), b.get("labs")
    if not la or not lb:
        return True
    return bool(set(la) & set(lb))


def classes_overlap(a: Entry, b: Entry) -> bool:
    """Hai mục có phạm vi lớp giao nhau không. Mục không khai ``classes`` coi như áp dụng mọi lớp."""
    ca, cb = a.get("classes"), b.get("classes")
    if not ca or not cb:
        return True
    return bool(set(ca) & set(cb))


def applies_to_class(entry: Entry, klass: str | None) -> bool:
    """Mục có áp dụng cho lớp ``klass`` không (``None`` = câu hỏi không nêu lớp)."""
    return not klass or not entry.get("classes") or klass in entry["classes"]


def class_from_text(text: str) -> str | None:
    """Lấy mã lớp được nhắc trong câu hỏi, ví dụ "Lab 3 lớp 3B" → ``"3B"``; không có thì ``None``."""
    match = re.search(r"\b(?:lop|class)\s*(\d[a-z])\b", config.strip_accents(text or ""))
    return match.group(1).upper() if match else None


def related_active(item: str, labs: list[int] | None = None, index: dict[str, Entry] | None = None,
                   exclude: str | None = None) -> list[Entry]:
    """Các mục ``active`` cùng hạng mục và giao phạm vi lab (ứng viên so trùng / cập nhật / mâu thuẫn)."""
    index = index or by_id()
    probe = {"labs": labs}
    return [e for e in index.values()
            if e.get("status") == "active" and e["item"] == item and e["id"] != exclude and labs_overlap(probe, e)]


def _linked(a: Entry, b: Entry) -> bool:
    """Hai mục có quan hệ thay thế hoặc ghi đè với nhau không."""
    if b["id"] in str(a.get("supersedes", "")).split(",") or a["id"] in str(b.get("supersedes", "")).split(","):
        return True
    return a["id"] in b.get("overrides", []) or b["id"] in a.get("overrides", [])


def find_conflicts(entry: Entry, index: dict[str, Entry] | None = None, klass: str | None = None) -> list[str]:
    """Mã các mục ``active`` khác mâu thuẫn với ``entry``.

    Mâu thuẫn khi: cùng hạng mục, giao phạm vi lab và lớp, khác ``deadline``, không liên kết thay thế/ghi đè. Nếu
    câu hỏi nêu lớp (``klass``), bỏ các mục không áp dụng cho lớp đó.
    """
    index = index or by_id()
    return [o["id"] for o in related_active(entry["item"], entry.get("labs"), index, exclude=entry["id"])
            if not _linked(entry, o) and o.get("deadline") != entry.get("deadline")
            and classes_overlap(entry, o) and applies_to_class(o, klass)]


def deadline_key(label: str) -> str:
    """Khoá so khớp một mốc hạn: ``CP3``, ``LAB5`` hoặc nhãn đã chuẩn hoá."""
    plain = config.strip_accents(label)
    match = re.search(r"\b(cp|lab)\s*(\d+)", plain)
    return f"{match.group(1)}{match.group(2)}".upper() if match else re.sub(r"\W+", " ", plain).strip()


def override_for(entry: Entry, lab: int | None = None, question: str = "",
                 index: dict[str, Entry] | None = None) -> Entry | None:
    """Tìm mục ghi đè một phần ``entry`` áp dụng cho câu hỏi hiện tại.

    Hai kiểu ghi đè:
        * Theo lab: mục có ``overrides`` chứa ``entry`` và ``labs`` chứa ``lab`` đang hỏi.
        * Theo mốc: mục có ``deadline_keys`` (ví dụ ``["CP3"]``) mà câu hỏi nhắc tới một trong các mốc đó.

    Args:
        entry: Mục đang được chọn làm nguồn.
        lab: Số lab đang hỏi (tuỳ chọn).
        question: Câu hỏi gốc, để so mốc được nhắc tới.
        index: Kết quả ``by_id()`` dùng lại.

    Returns:
        Mục đang hiệu lực nên dùng thay ``entry``, hoặc ``None``.
    """
    index = index or by_id()
    asked_keys = {deadline_key(m) for m in re.findall(r"(?i)\b(?:cp|lab)\s*\d+", config.strip_accents(question))}
    for other in index.values():
        if other.get("status") != "active" or entry["id"] not in other.get("overrides", []):
            continue
        if lab is not None and lab in (other.get("labs") or []):
            return other
        if asked_keys & set(other.get("deadline_keys", [])):
            return other
    return None


def partial_updates(entry: Entry, index: dict[str, Entry] | None = None) -> list[Entry]:
    """Các mục đang hiệu lực ghi đè một phần ``entry`` (để cảnh báo "một số mốc đã được cập nhật")."""
    index = index or by_id()
    return [o for o in index.values() if o.get("status") == "active" and entry["id"] in o.get("overrides", [])]


def _next_id(prefix: str) -> str:
    """Sinh mã kế tiếp cho mục runtime, ví dụ ``SRC-03``."""
    existing = [e["id"] for e in read_json(ENTRIES_FILE, []) if e["id"].startswith(prefix + "-")]
    return f"{prefix}-{len(existing) + 1:02d}"


def _replacement_mode(new: Entry, old: Entry) -> str:
    """Cách mục mới tác động mục cũ: ``labs`` / ``deadlines`` (ghi đè một phần) hoặc ``full`` (thay toàn bộ)."""
    labs = new.get("labs")
    if labs and old.get("labs") and set(old["labs"]) - set(labs):
        return "labs"
    old_keys = {deadline_key(d["label"]) for d in old.get("deadlines") or []}
    new_keys = {deadline_key(d["label"]) for d in new.get("deadlines") or []}
    if len(old_keys) > 1 and new_keys and new_keys < old_keys:
        return "deadlines"
    return "full"


def add_entry(entry: Entry, supersedes: list[str] | None = None) -> Entry:
    """Ghi một mục mới vào sổ runtime và xử lý quan hệ với các mục cũ.

    Với mỗi mã trong ``supersedes``:
        * Mục cũ rộng hơn về lab (Lab 1–4 so với Lab 3) → ghi đè cục bộ theo lab.
        * Mục cũ có nhiều mốc và mục mới chỉ đổi một phần (CP3 trong CP1–CP5) → ghi đè cục bộ theo mốc;
          các mốc còn lại vẫn lấy từ mục cũ.
        * Còn lại → thay thế toàn bộ (mục cũ thành ``superseded``).

    Args:
        entry: Dict mục đã đủ trường nội dung (chưa cần ``id``/``status``).
        supersedes: Mã các mục bị mục mới thay thế.

    Returns:
        Mục đã lưu (có ``id``, ``status``).
    """
    with locked(ENTRIES_FILE):
        prefix = "TA" if entry.get("kind") == "ta_answer" else "SRC"
        entry = {**entry, "id": _next_id(prefix), "status": "active"}
        replaced = _apply_supersedes(entry, supersedes or [])
        if replaced:
            entry["supersedes"] = ",".join(replaced)
        write_json(ENTRIES_FILE, read_json(ENTRIES_FILE, []) + [entry])
    return entry


def _apply_supersedes(entry: Entry, supersedes: list[str]) -> list[str]:
    """Ghi quan hệ thay thế/ghi đè cho ``entry``; trả mã các mục bị thay thế toàn bộ."""
    index = by_id()
    replaced = []
    with locked(OVERRIDE_FILE):
        overrides = read_json(OVERRIDE_FILE, {})
        for old_id in supersedes:
            old = index.get(old_id)
            if not old:
                continue
            mode = _replacement_mode(entry, old)
            if mode == "full":
                overrides[old_id] = entry["id"]
                replaced.append(old_id)
                continue
            entry.setdefault("overrides", []).append(old_id)
            if mode == "deadlines":
                entry["deadline_keys"] = sorted({deadline_key(d["label"]) for d in entry["deadlines"]})
        write_json(OVERRIDE_FILE, overrides)
    return replaced


def add_ta_entry(item: str, content: dict[str, str], ta_name: str, question: str,
                 labs: list[int] | None = None, supersedes: list[str] | None = None) -> Entry:
    """Thêm câu trả lời TA cho một cụm hàng chờ thành mục nguồn ``TA-xx``.

    Args:
        item: Hạng mục.
        content: ``{"where", "how", "deadline", "who"}`` do TA nhập (``who`` có thể rỗng).
        ta_name: Tên hiển thị người duyệt.
        question: Câu hỏi đại diện của cụm, dùng làm tiêu đề.
        labs: Danh sách số lab áp dụng.
        supersedes: Mã các mục bị thay thế (cụm CONFLICT truyền các nguồn đang mâu thuẫn).

    Returns:
        Mục vừa tạo.
    """
    where, how, deadline = content["where"], content["how"], content["deadline"]
    entry: Entry = {
        "kind": "ta_answer", "origin": "ta", "item": item,
        "scope": "TA xác nhận theo câu hỏi học viên", "title": f"TA xác nhận: {question[:80]}",
        "published": config.now().strftime("%Y-%m-%d %H:%M"), "source": f"TA {ta_name} duyệt", "url": None,
        "who": content.get("who") or "Không ghi rõ", "where": where, "how": how, "deadline": deadline,
        "consequence": "Không ghi rõ", "quote": f"{where} — {how} — hạn: {deadline}",
    }
    if labs:
        entry["labs"] = labs
    return add_entry(entry, supersedes)


def parse_due(value: str | None) -> datetime | None:
    """Đọc thời điểm ``YYYY-MM-DDTHH:MM``; ``None`` nếu sai định dạng."""
    try:
        return datetime.strptime(value or "", "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _overridden_keys(entry: Entry, index: dict[str, Entry]) -> set[str]:
    """Các mốc của ``entry`` đã bị mục khác ghi đè theo mốc."""
    return {k for o in partial_updates(entry, index) for k in o.get("deadline_keys", [])}


def _entry_deadlines(entry: Entry, start: datetime, until: datetime, index: dict[str, Entry]) -> list[dict[str, Any]]:
    """Các mốc hạn của một mục nằm trong ``(start, until]``, bỏ mốc đã bị ghi đè và mốc trùng."""
    base = {"entry_id": entry["id"], "item": entry["item"], "title": entry["title"],
            "source": entry.get("source"), "url": entry.get("url")}
    skip = _overridden_keys(entry, index)
    found: dict[datetime, dict[str, Any]] = {}
    for d in entry.get("deadlines") or []:
        due = parse_due(d.get("due_at"))
        if due and start < due <= until and deadline_key(d.get("label", "")) not in skip:
            found.setdefault(due, {**base, "label": d.get("label") or entry["title"], "due_at": due})
    close = entry.get("recurring_daily_close")
    if close:
        hh, mm = (int(x) for x in close.split(":"))
        due = start.replace(hour=hh, minute=mm, second=0, microsecond=0)
        due += timedelta(days=1) if due <= start else timedelta()
        while due <= until:
            found.setdefault(due, {**base, "label": f"{entry['title']} (đóng {close})", "due_at": due})
            due += timedelta(days=1)
    return list(found.values())


def upcoming_deadlines(now: datetime | None = None, hours: float = 48, item: str | None = None) -> list[dict[str, Any]]:
    """Liệt kê hạn nộp sắp tới từ các mục đang hiệu lực.

    Gồm hạn tuyệt đối (``deadlines``) và hạn lặp mỗi ngày (``recurring_daily_close``). Bài lab có hạn tương đối
    ("23:59 ngày học lab") không có mốc tuyệt đối nên không nằm trong danh sách.

    Args:
        now: Thời điểm tính (mặc định ``config.now()``).
        hours: Độ dài cửa sổ nhìn trước.
        item: Chỉ lấy một hạng mục (tuỳ chọn).

    Returns:
        ``{"entry_id", "item", "label", "due_at", "title", "source", "url"}`` sắp theo ``due_at``.
    """
    start = now or config.now()
    until = start + timedelta(hours=hours)
    index = by_id()
    out = []
    for entry in index.values():
        if entry.get("status") == "active" and (not item or entry["item"] == item):
            out += _entry_deadlines(entry, start, until, index)
    return sorted(out, key=lambda x: x["due_at"])
