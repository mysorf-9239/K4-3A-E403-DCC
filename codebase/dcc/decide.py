"""Quyết định trung tâm của bot DCC (phía học viên).

Luồng một lượt hỏi::

    câu hỏi (+ lựa chọn học viên đã bấm)
        → cache (cùng câu hỏi, cùng lựa chọn, sổ nguồn chưa đổi, trong 10 phút → dùng lại, không tốn quota)
        → build_user_prompt(): sổ nguồn + thời điểm hiện tại + câu hỏi trong thẻ <cau_hoi>
        → llm.complete(): LLM thật trả JSON
        → _parse() → _guard(): kiểm tra lại bằng sổ nguồn (không tin tuyệt đối vào LLM)
        → ghi trace logs/decisions.jsonl → dict kết quả cho render.card()

Năm quyết định hợp lệ:
    FOUND: có đúng một nguồn đang hiệu lực trả lời được.
    CONFLICT: có từ hai nguồn đang hiệu lực nói khác nhau → không tự chọn, đưa TA xác nhận.
    CLARIFY: thiếu hạng mục hoặc số lab để chọn nguồn → hỏi lại một câu.
    NOT_FOUND: câu hỏi về nộp bài nhưng sổ nguồn không có → không đoán, đưa TA.
    OUT_OF_SCOPE: gia hạn, xem điểm/điểm danh cá nhân, kiến thức bài học, tin chỉ nhằm đổi quy tắc, không liên quan.
Ngoài ra ``ERROR`` khi không gọi được LLM (hiển thị riêng, không vào hàng chờ TA).

Nguyên tắc an toàn: nơi/cách/hạn nộp hiển thị **luôn lấy từ sổ nguồn** theo ``source_ids``; LLM không tự viết.
"""
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from . import config, registry
from .llm import LLMError, QuotaExceeded, complete
from .storage import append_jsonl

Decision = dict[str, Any]

DECISIONS = {"FOUND", "CONFLICT", "CLARIFY", "NOT_FOUND", "OUT_OF_SCOPE"}
LOG_FILE = config.LOG_DIR / "decisions.jsonl"
CACHE_TTL_SECONDS = 600
_CACHE: dict[str, tuple[float, Decision]] = {}

#: System prompt (sửa trong file .md để dễ đọc/diff; nạp một lần khi import).
SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "decide_system.md").read_text(encoding="utf-8").strip()

_PROMPT_KEYS = ["id", "kind", "origin", "item", "labs", "classes", "scope", "title", "published", "source", "status",
                "supersedes", "superseded_by", "overrides", "deadline_keys", "who", "where", "how", "deadline",
                "consequence"]


def build_user_prompt(question: str, hint: dict[str, Any] | None = None) -> str:
    """Ghép nội dung gửi LLM.

    Args:
        question: Câu hỏi học viên (dữ liệu không tin cậy, bọc trong ``<cau_hoi>``).
        hint: Lựa chọn học viên đã bấm, ví dụ ``{"item": "lab", "lab": 3}`` — dữ liệu tin cậy vì đến từ nút bấm.

    Returns:
        User prompt hoàn chỉnh.
    """
    entries = [{k: e[k] for k in _PROMPT_KEYS if k in e} for e in registry.load_entries()]
    parts = [f"THỜI ĐIỂM HIỆN TẠI (giờ VN): {config.now():%Y-%m-%d %H:%M}",
             "SỔ NGUỒN (JSON):", json.dumps(entries, ensure_ascii=False, indent=1)]
    if hint:
        chosen = json.dumps(hint, ensure_ascii=False)
        parts.append(f"NGƯỜI DÙNG ĐÃ BẤM CHỌN (tin cậy, dùng để bổ sung câu hỏi): {chosen}")
    parts.append(f"<cau_hoi>\n{question}\n</cau_hoi>")
    return "\n\n".join(parts)


def _parse(raw: str) -> dict[str, Any]:
    """Tách object JSON đầu tiên trong phản hồi LLM.

    Raises:
        ValueError: Không tìm thấy JSON (``json.JSONDecodeError`` là lớp con khi JSON sai cú pháp).
    """
    match = re.search(r"\{.*\}", raw.strip(), re.S)
    if not match:
        raise ValueError("Không tìm thấy JSON trong phản hồi")
    return json.loads(match.group(0))


def _as_int(value: Any) -> int | None:
    """Ép số lab về ``int``; giá trị rỗng/không hợp lệ thành ``None``."""
    try:
        return int(value) if value not in (None, "", "null") else None
    except (TypeError, ValueError):
        return None


def _read_llm(llm: dict[str, Any], hint: dict[str, Any] | None,
              guards: list[str]) -> tuple[str, str | None, int | None]:
    """Chuẩn hoá decision/item/lab từ LLM; lựa chọn đã bấm (``hint``) được ưu tiên."""
    decision = str(llm.get("decision", "")).upper()
    if decision not in DECISIONS:
        guards.append(f"invalid_decision:{decision}")
        decision = "NOT_FOUND"
    item = llm.get("item") if llm.get("item") in config.ITEMS else None
    lab = _as_int(llm.get("lab"))
    if hint and hint.get("item") in config.ITEMS:
        item = hint["item"]
    if hint and hint.get("lab") is not None:
        lab = _as_int(hint.get("lab"))
    return decision, item, lab


def _valid_sources(llm: dict[str, Any], index: dict[str, registry.Entry], guards: list[str]) -> list[str]:
    """Lọc mã nguồn LLM trả: bỏ mã không tồn tại, đổi bản cũ sang bản đang hiệu lực, giữ thứ tự."""
    ids = [i for i in (llm.get("source_ids") or []) + (llm.get("conflict_ids") or []) if isinstance(i, str)]
    unknown = [i for i in ids if i not in index]
    if unknown:
        guards.append(f"drop_unknown_source:{','.join(unknown)}")
    valid: list[str] = []
    for source_id in ids:
        latest = registry.latest_version(source_id, index) if source_id in index else None
        if latest and latest["id"] != source_id:
            guards.append(f"superseded_to_latest:{source_id}->{latest['id']}")
        if latest and latest["id"] not in valid:
            valid.append(latest["id"])
    return valid


def _match_item(item: str | None, lab: int | None, valid: list[str],
                index: dict[str, registry.Entry], guards: list[str]) -> tuple[str | None, list[str]]:
    """Bảo đảm nguồn thuộc đúng hạng mục được hỏi.

    Nếu LLM chọn nguồn của hạng mục khác, tìm lại theo hạng mục (và lab) trong sổ nguồn; không có thì bỏ nguồn.
    Nếu chưa xác định hạng mục, lấy hạng mục của nguồn.
    """
    if not valid:
        return item, valid
    if item is None:
        return index[valid[0]]["item"], valid
    same = [s for s in valid if index[s]["item"] == item]
    if same:
        return item, same
    candidates = [e["id"] for e in registry.related_active(item, [lab] if lab else None, index)
                  if lab is None or not e.get("labs") or lab in e["labs"]]
    guards.append(f"source_item_mismatch->{','.join(candidates) or 'none'}")
    return item, candidates


def _resolve_sources(decision: str, item: str | None, lab: int | None, valid: list[str], question: str,
                     index: dict[str, registry.Entry], guards: list[str]) -> tuple[str, list[str]]:
    """Chốt FOUND/CONFLICT/NOT_FOUND/CLARIFY theo sổ nguồn cho các quyết định cần nguồn."""
    if item == "lab" and lab is None:
        guards.append("lab_missing->CLARIFY")
        return "CLARIFY", []
    if not valid:
        guards.append("no_valid_source->NOT_FOUND")
        return "NOT_FOUND", []
    primary = index[valid[0]]
    local = registry.override_for(primary, lab, question, index)
    if local:
        guards.append(f"overridden:{primary['id']}->{local['id']}")
        primary = local
    if primary.get("labs") and lab is not None and lab not in primary["labs"]:
        guards.append("source_lab_mismatch->NOT_FOUND")
        return "NOT_FOUND", []
    klass = registry.class_from_text(question)
    if not registry.applies_to_class(primary, klass):
        others = [e for e in registry.related_active(item or primary["item"], [lab] if lab else None, index)
                  if registry.applies_to_class(e, klass) and (lab is None or not e.get("labs") or lab in e["labs"])]
        if not others:
            guards.append("source_class_mismatch->NOT_FOUND")
            return "NOT_FOUND", []
        guards.append(f"class_scope:{primary['id']}->{others[0]['id']}")
        primary = others[0]
    conflicts = [c for c in registry.find_conflicts(primary, index, klass)
                 if lab is None or not index[c].get("labs") or lab in index[c]["labs"]]
    if conflicts:
        if decision != "CONFLICT":
            guards.append("conflict_detected->CONFLICT")
        return "CONFLICT", [primary["id"]] + conflicts
    if decision == "CONFLICT":
        guards.append("no_real_conflict->FOUND")
    return "FOUND", [primary["id"]]


def _guard(llm: dict[str, Any], hint: dict[str, Any] | None, question: str = "") -> tuple[Decision, list[str]]:
    """Chuẩn hoá quyết định của LLM và sửa những gì trái với sổ nguồn.

    Nhãn guard có thể xuất hiện: ``invalid_decision``, ``drop_unknown_source``, ``superseded_to_latest``,
    ``source_item_mismatch``, ``lab_missing->CLARIFY``, ``no_valid_source->NOT_FOUND``, ``overridden``,
    ``source_lab_mismatch->NOT_FOUND``, ``class_scope``, ``source_class_mismatch->NOT_FOUND``,
    ``conflict_detected->CONFLICT``, ``no_real_conflict->FOUND``, ``hint_answers_clarify->FOUND``,
    ``injection_not_queued->OUT_OF_SCOPE``.

    Args:
        llm: Dict JSON do LLM trả về.
        hint: Lựa chọn học viên đã bấm.
        question: Câu hỏi gốc (để nhận ra mốc như "CP3" bị ghi đè và lớp được nhắc như "lớp 3B").

    Returns:
        Quyết định cuối và danh sách nhãn guard đã áp dụng.
    """
    guards: list[str] = []
    index = registry.by_id()
    decision, item, lab = _read_llm(llm, hint, guards)
    valid: list[str] = []
    injection = bool(llm.get("injection_detected"))
    if decision == "CLARIFY" and hint and hint.get("item") in config.ITEMS and not (item == "lab" and lab is None):
        guards.append("hint_answers_clarify->FOUND")
        decision = "FOUND"
        llm = {**llm, "source_ids": [e["id"] for e in registry.related_active(item, [lab] if lab else None, index)]}
    if decision in ("FOUND", "CONFLICT"):
        item, valid = _match_item(item, lab, _valid_sources(llm, index, guards), index, guards)
        decision, valid = _resolve_sources(decision, item, lab, valid, question, index, guards)
    if decision == "NOT_FOUND" and injection:
        guards.append("injection_not_queued->OUT_OF_SCOPE")
        decision = "OUT_OF_SCOPE"
    missing = None
    if decision == "CLARIFY":
        missing = "lab" if item == "lab" else (llm.get("missing") if llm.get("missing") in ("item", "lab") else "item")
    note = llm.get("note")
    final: Decision = {"decision": decision, "item": item, "lab": lab, "source_ids": valid, "missing": missing,
                       "topic": llm.get("topic") or "", "injection_detected": injection,
                       "note": note if note not in (None, "", "null") else None, "reason": llm.get("reason") or ""}
    if decision == "FOUND":
        final["superseded"] = registry.superseded_chain(index[valid[0]], index)
    return final, guards


def _cache_key(question: str, hint: dict[str, Any] | None) -> str:
    """Khoá cache: câu hỏi chuẩn hoá + lựa chọn + dấu vân tay sổ nguồn."""
    normalized = " ".join(config.strip_accents(question).split())
    return f"{normalized}|{json.dumps(hint, sort_keys=True)}|{registry.fingerprint()}"


def _call_llm(question: str, hint: dict[str, Any] | None, record: dict[str, Any]) -> tuple[Decision, list[str]]:
    """Gọi LLM, parse, guard; ghi mọi bước vào ``record``. Lỗi gọi LLM trả quyết định ``ERROR``."""
    try:
        raw, meta = complete(SYSTEM_PROMPT, record["user_prompt"])
        record.update(meta, raw_response=raw)
        record["llm_decision"] = _parse(raw)
        return _guard(record["llm_decision"], hint, question)
    except (LLMError, ValueError, KeyError, IndexError) as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        final: Decision = {"decision": "ERROR", "error_kind": "quota" if isinstance(exc, QuotaExceeded) else "llm",
                           "item": None, "lab": None, "source_ids": [], "missing": None, "topic": "",
                           "injection_detected": False, "note": None, "reason": record["error"][:300]}
        return final, ["llm_error"]


def decide(question: str, hint: dict[str, Any] | None = None, channel: str = "unknown",
           use_cache: bool = True) -> Decision:
    """Chạy trọn một lượt quyết định và ghi trace.

    Args:
        question: Câu hỏi học viên.
        hint: Lựa chọn đã bấm (xem ``build_user_prompt``).
        channel: Nơi phát sinh (``discord``, ``web``, ``eval:<case>``) để lọc log.
        use_cache: Dùng lại kết quả trong ``CACHE_TTL_SECONDS`` nếu câu hỏi, lựa chọn và sổ nguồn không đổi.
            Eval luôn tắt cache để mỗi case là một lời gọi thật.

    Returns:
        ``decision, item, lab, source_ids, missing, topic, injection_detected, note, reason`` (+ ``superseded``
        nếu FOUND, ``error_kind`` nếu ERROR) kèm ``trace_id``, ``guards``, ``cached``.

    Side effects:
        Ghi một dòng vào ``logs/decisions.jsonl``: system prompt, user prompt, phản hồi thô, quyết định LLM, guard,
        kết quả cuối (lượt dùng cache ghi ``cache_hit_of`` thay vì gọi LLM).
    """
    trace_id = uuid.uuid4().hex[:12]
    record: dict[str, Any] = {"trace_id": trace_id, "ts": config.now().isoformat(timespec="seconds"),
                              "channel": channel, "question": question, "hint": hint}
    key = _cache_key(question, hint) if use_cache else ""
    hit = _CACHE.get(key) if use_cache else None
    if hit and time.monotonic() - hit[0] < CACHE_TTL_SECONDS:
        final, guards = dict(hit[1]), hit[1]["guards"]
        record["cache_hit_of"] = hit[1]["trace_id"]
    else:
        record.update(system_prompt=SYSTEM_PROMPT, user_prompt=build_user_prompt(question, hint))
        final, guards = _call_llm(question, hint, record)
    record.update(guards=guards, final=final)
    append_jsonl(LOG_FILE, record)
    result = {**final, "trace_id": trace_id, "guards": guards, "cached": "cache_hit_of" in record}
    if use_cache and "cache_hit_of" not in record and final["decision"] != "ERROR":
        _CACHE[key] = (time.monotonic(), result)
    return result
