"""Nạp nguồn: biến một thông báo (tin Discord, đoạn tài liệu công khai) thành đề xuất mục nguồn cho TA duyệt.

Đây là lần dùng AI thứ hai của hệ thống, ở phía TA, mức **augment**: AI chỉ đề xuất, TA quyết định (và có thể sửa)
trước khi ghi vào sổ. Lý do: ghi sai sổ nguồn là trả lời sai cho *mọi* học viên sau đó.

Luồng::

    văn bản thông báo + nguồn (kênh/url)
        → LLM trích xuất 0..n mục và phân loại quan hệ với sổ nguồn
        → _check_candidate(): kiểm tra bằng code (hạng mục, trích dẫn nguyên văn, mốc giờ, mã liên quan, so lại
          với các mục active cùng phạm vi)
        → lưu đề xuất data/runtime/proposals.json + trace logs/ingest.jsonl
        → TA: approve(..., edits=...) ghi vào sổ · reject()

Quan hệ (relation):
    NEW: chưa có mục active nào cùng hạng mục/phạm vi.
    UPDATE: thay thế mục cũ (``related_ids``) — thông báo nói rõ cập nhật/đổi.
    CONFLICT: khác hạn với mục cũ nhưng không nói là thay thế → TA chọn "thay thế" hoặc "giữ song song".
    DUPLICATE: trùng nội dung mục đã có → không cho duyệt, chỉ bỏ qua.
"""
import json
import re
import uuid
from pathlib import Path
from typing import Any

from . import config, registry
from .llm import LLMError, QuotaExceeded, complete
from .storage import append_jsonl, locked, read_json, write_json

Proposal = dict[str, Any]

PROPOSAL_FILE = config.RUNTIME_DIR / "proposals.json"
LOG_FILE = config.LOG_DIR / "ingest.jsonl"
RELATIONS = {"NEW", "UPDATE", "CONFLICT", "DUPLICATE"}
EDITABLE_FIELDS = ("who", "where", "how", "deadline")

#: System prompt (sửa trong file .md để dễ đọc/diff; nạp một lần khi import).
SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "ingest_system.md").read_text(encoding="utf-8").strip()

_PROMPT_KEYS = ["id", "item", "labs", "scope", "title", "published", "source", "status", "supersedes",
                "superseded_by", "overrides", "deadline_keys", "who", "where", "how", "deadline",
                "recurring_daily_close"]


def _norm(text: str | None) -> str:
    """Chuẩn hoá khoảng trắng và chữ thường để so trích dẫn / hạn nộp."""
    return re.sub(r"\s+", " ", text or "").strip().lower()


def build_user_prompt(text: str, published: str) -> str:
    """Ghép sổ nguồn (rút gọn), thời điểm đăng và thông báo trong thẻ ``<thong_bao>``."""
    entries = [{k: e[k] for k in _PROMPT_KEYS if k in e} for e in registry.load_entries()]
    return "\n\n".join([f"THỜI ĐIỂM ĐĂNG THÔNG BÁO (giờ VN): {published}", "SỔ NGUỒN (JSON):",
                        json.dumps(entries, ensure_ascii=False, indent=1), f"<thong_bao>\n{text}\n</thong_bao>"])


def normalize_due(value: Any) -> str | None:
    """Chuẩn hoá mốc giờ về ``YYYY-MM-DDTHH:MM``; chấp nhận dấu cách thay ``T`` và phần giây thừa.

    Returns:
        Chuỗi chuẩn, hoặc ``None`` nếu không phải một mốc giờ đầy đủ ngày + giờ.
    """
    match = re.fullmatch(r"\s*(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::\d{2})?\s*", str(value or ""))
    due = f"{match.group(1)}T{match.group(2)}" if match else None
    return due if registry.parse_due(due) else None


def _clean_deadlines(raw: list[dict[str, Any]] | None, fallback_label: str, guards: list[str]) -> list[dict[str, str]]:
    """Giữ các mốc có ``due_at`` đọc được (đã chuẩn hoá); ghi guard ``bad_due_at`` cho mốc bị bỏ."""
    out = []
    for item in raw or []:
        due = normalize_due(item.get("due_at"))
        if due:
            out.append({"label": item.get("label") or fallback_label, "due_at": due})
        else:
            guards.append(f"bad_due_at:{item.get('due_at')}")
    return out


def _build_entry(c: dict[str, Any], text: str, guards: list[str]) -> registry.Entry:
    """Tạo mục nguồn chuẩn hoá từ một mục LLM trích xuất (chưa có nguồn/ngày đăng)."""
    quote = c.get("quote") or ""
    if not quote or _norm(quote) not in _norm(text):
        guards.append("quote_not_verbatim")
        quote = text.strip()[:200]
    entry: registry.Entry = {"kind": "official", "origin": "ingested", "item": c["item"],
                             "scope": c.get("scope") or "Không ghi rõ",
                             "title": c.get("title") or config.ITEMS[c["item"]],
                             "consequence": c.get("consequence") or "Không ghi rõ", "quote": quote}
    entry.update({f: c.get(f) or "Không ghi rõ" for f in EDITABLE_FIELDS})
    labs = [int(x) for x in (c.get("labs") or []) if str(x).isdigit()]
    if labs:
        entry["labs"] = labs
    deadlines = _clean_deadlines(c.get("deadlines"), entry["title"], guards)
    if deadlines:
        entry["deadlines"] = deadlines
    close = c.get("recurring_daily_close")
    if close and re.fullmatch(r"\d{2}:\d{2}", str(close)):
        entry["recurring_daily_close"] = close
    elif close:
        guards.append(f"bad_daily_close:{close}")
    return entry


def _check_relation(c: dict[str, Any], entry: registry.Entry, guards: list[str]) -> tuple[str, list[str]]:
    """Kiểm tra quan hệ LLM trả bằng sổ nguồn: mã liên quan phải active; NEW mà đã có mục cùng phạm vi thì đổi."""
    index = registry.by_id()
    raw_related = c.get("related_ids") or []
    related = [i for i in raw_related if i in index and index[i].get("status") == "active"]
    if len(related) != len(raw_related):
        guards.append("drop_unknown_related")
    relation = str(c.get("relation", "NEW")).upper()
    relation = relation if relation in RELATIONS else "NEW"
    candidates = registry.related_active(entry["item"], entry.get("labs"), index)
    if relation == "NEW" and candidates:
        same = [e["id"] for e in candidates if _norm(e.get("deadline")) == _norm(entry["deadline"])]
        relation, related = ("DUPLICATE", same) if same else ("CONFLICT", [e["id"] for e in candidates])
        guards.append("duplicate_detected" if same else "new_but_related_exists->CONFLICT")
    if relation != "NEW" and not related:
        guards.append(f"{relation.lower()}_without_target->NEW")
        relation = "NEW"
    return relation, related


def _check_candidate(c: dict[str, Any], text: str) -> tuple[Proposal | None, list[str]]:
    """Kiểm tra một mục LLM trích xuất; trả ``({"entry", "relation", "related_ids", "reason"} | None, guards)``."""
    if c.get("item") not in config.ITEMS:
        return None, [f"invalid_item:{c.get('item')}"]
    guards: list[str] = []
    entry = _build_entry(c, text, guards)
    relation, related = _check_relation(c, entry, guards)
    return {"entry": entry, "relation": relation, "related_ids": related, "reason": c.get("reason") or ""}, guards


def _extract(text: str, meta: dict[str, Any], record: dict[str, Any], result: dict[str, Any]) -> None:
    """Gọi LLM, parse và kiểm tra từng mục; ghi đề xuất vào ``result['proposals']``."""
    raw, llm_meta = complete(SYSTEM_PROMPT, record["user_prompt"])
    record.update(llm_meta, raw_response=raw)
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("Không tìm thấy JSON trong phản hồi")
    parsed = json.loads(match.group(0))
    record["llm_output"] = parsed
    result.update(is_submission_notice=bool(parsed.get("is_submission_notice")),
                  injection_detected=bool(parsed.get("injection_detected")))
    for c in parsed.get("entries") or []:
        cand, guards = _check_candidate(c, text)
        result["guards"] += guards
        if cand:
            cand["entry"].update(source=meta["source"], url=meta["url"], published=meta["published"])
            result["proposals"].append({"status": "pending", "trace_id": record["trace_id"],
                                        "created": config.now().strftime("%Y-%m-%d %H:%M"),
                                        "message_id": meta["message_id"], "review_message_id": None,
                                        **cand, "guards": guards})


def _store(proposals: list[Proposal]) -> None:
    """Gán mã ``P-xxx`` và lưu đề xuất mới, có khoá."""
    with locked(PROPOSAL_FILE):
        existing = read_json(PROPOSAL_FILE, [])
        for offset, proposal in enumerate(proposals, start=1):
            proposal["id"] = f"P-{len(existing) + offset:03d}"
        write_json(PROPOSAL_FILE, existing + proposals)


def propose(text: str, source: str, url: str | None = None, published: str | None = None,
            channel: str = "unknown", message_id: int | None = None) -> dict[str, Any]:
    """Trích xuất một thông báo thành các đề xuất chờ TA duyệt.

    Args:
        text: Nội dung thông báo.
        source: Nhãn nguồn hiển thị, ví dụ ``#announcements`` hoặc ``README repo đề``.
        url: Link tới thông báo/tài liệu gốc (tuỳ chọn).
        published: Thời điểm đăng ``YYYY-MM-DD HH:MM`` (mặc định hiện tại, giờ VN).
        channel: Nơi phát sinh (``discord-auto``, ``discord-menu``, ``web``, ``eval:<id>``).
        message_id: ID tin nhắn Discord gốc (tuỳ chọn).

    Returns:
        ``{"trace_id", "is_submission_notice", "injection_detected", "proposals", "guards", "error"}``; mỗi đề xuất
        có ``id``, ``status="pending"``, ``relation``, ``related_ids``, ``entry``. Đề xuất eval có mã ``EVAL-n``.

    Side effects:
        Lưu đề xuất (trừ ``channel`` bắt đầu bằng ``eval:``) và ghi trace ``logs/ingest.jsonl``.
    """
    meta = {"source": source, "url": url, "message_id": message_id,
            "published": published or config.now().strftime("%Y-%m-%d %H:%M")}
    trace_id = uuid.uuid4().hex[:12]
    record: dict[str, Any] = {"trace_id": trace_id, "ts": config.now().isoformat(timespec="seconds"),
                              "channel": channel, **meta, "text": text, "system_prompt": SYSTEM_PROMPT,
                              "user_prompt": build_user_prompt(text, meta["published"])}
    result: dict[str, Any] = {"trace_id": trace_id, "is_submission_notice": False, "injection_detected": False,
                              "proposals": [], "guards": [], "error": None}
    try:
        _extract(text, meta, record, result)
    except (LLMError, ValueError, KeyError, IndexError) as exc:
        result["error"] = "quota" if isinstance(exc, QuotaExceeded) else f"{type(exc).__name__}: {exc}"[:300]
    if channel.startswith("eval:"):
        for n, proposal in enumerate(result["proposals"], start=1):
            proposal["id"] = f"EVAL-{n}"
    elif result["proposals"]:
        _store(result["proposals"])
    record["result"] = result
    append_jsonl(LOG_FILE, record)
    return result


def list_proposals(status: str | None = "pending") -> list[Proposal]:
    """Liệt kê đề xuất theo trạng thái (``pending`` | ``approved`` | ``rejected`` | ``None``)."""
    return [p for p in read_json(PROPOSAL_FILE, []) if status is None or p["status"] == status]


def get(proposal_id: str) -> Proposal | None:
    """Lấy một đề xuất theo mã; ``None`` nếu không có."""
    return next((p for p in read_json(PROPOSAL_FILE, []) if p["id"] == proposal_id), None)


def _update(proposal_id: str, **fields: Any) -> None:
    """Cập nhật các trường của một đề xuất, có khoá."""
    with locked(PROPOSAL_FILE):
        items = read_json(PROPOSAL_FILE, [])
        for proposal in items:
            if proposal["id"] == proposal_id:
                proposal.update(fields)
        write_json(PROPOSAL_FILE, items)


def set_review_message(proposal_id: str, message_id: int) -> None:
    """Lưu ID tin nhắn duyệt trong kênh TA."""
    _update(proposal_id, review_message_id=message_id)


def parse_deadlines_text(text: str) -> list[dict[str, str]]:
    """Đọc ô "mốc giờ" TA sửa: mỗi dòng ``nhãn | YYYY-MM-DDTHH:MM``.

    Raises:
        ValueError: Dòng sai định dạng (thông báo rõ dòng nào để TA sửa).
    """
    out = []
    for line in filter(None, (ln.strip() for ln in text.splitlines())):
        label, _, raw_due = line.rpartition("|")
        due = normalize_due(raw_due)
        if not label.strip() or not due:
            raise ValueError(f"Mốc giờ sai định dạng: '{line}' (cần 'nhãn | YYYY-MM-DDTHH:MM')")
        out.append({"label": label.strip(), "due_at": due})
    return out


def deadlines_to_text(deadlines: list[dict[str, str]] | None) -> str:
    """Hiển thị mốc giờ thành văn bản để TA sửa (ngược của ``parse_deadlines_text``)."""
    return "\n".join(f"{d['label']} | {d['due_at']}" for d in deadlines or [])


def _apply_edits(entry: registry.Entry, edits: dict[str, str] | None) -> tuple[registry.Entry, bool]:
    """Áp nội dung TA sửa vào mục; trả ``(mục mới, có sửa hay không)``."""
    if not edits:
        return entry, False
    new = dict(entry)
    for field in EDITABLE_FIELDS:
        if edits.get(field, "").strip():
            new[field] = edits[field].strip()
    if "deadlines" in edits:
        parsed = parse_deadlines_text(edits["deadlines"])
        if parsed:
            new["deadlines"] = parsed
        else:
            new.pop("deadlines", None)
    return new, new != entry


def approve(proposal_id: str, reviewer: str, replace: bool | None = None,
            edits: dict[str, str] | None = None) -> registry.Entry:
    """TA duyệt đề xuất thành mục nguồn ``SRC-xx``, có thể sửa nội dung trước.

    Args:
        proposal_id: Mã đề xuất.
        reviewer: Tên người duyệt.
        replace: ``True`` thay thế ``related_ids``; ``False`` thêm song song; ``None`` = thay thế khi ``UPDATE``.
        edits: Nội dung TA sửa: ``who``, ``where``, ``how``, ``deadline``, ``deadlines`` (văn bản nhiều dòng).

    Returns:
        Mục nguồn vừa tạo.

    Raises:
        ValueError: Đề xuất không tồn tại / đã xử lý / là ``DUPLICATE``, hoặc mốc giờ TA sửa sai định dạng.
    """
    proposal = get(proposal_id)
    if not proposal or proposal["status"] != "pending":
        raise ValueError("Đề xuất không tồn tại hoặc đã xử lý")
    if proposal["relation"] == "DUPLICATE":
        raise ValueError("Đề xuất trùng mục đã có; hãy bỏ qua")
    entry, edited = _apply_edits(proposal["entry"], edits)
    if edited:
        entry["reviewed_edit"] = True
    replace = proposal["relation"] == "UPDATE" if replace is None else replace
    saved = registry.add_entry(entry, proposal["related_ids"] if replace else None)
    _update(proposal_id, status="approved", reviewer=reviewer, entry_id=saved["id"], replaced=bool(replace),
            edited=edited, reviewed_at=config.now().strftime("%Y-%m-%d %H:%M"))
    return saved


def reject(proposal_id: str, reviewer: str) -> None:
    """TA bỏ qua đề xuất."""
    _update(proposal_id, status="rejected", reviewer=reviewer, reviewed_at=config.now().strftime("%Y-%m-%d %H:%M"))
