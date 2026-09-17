"""Bản tin cho TA — thay cho bản tin "Học viên đang hỏi gì" hiện tại của bot Kute.

Bản tin của Kute trong ``discord-pack`` do LLM tóm tắt tự do nên có lỗi thật (chuỗi "nguồn tham chiếu" chèn giữa từ,
tóm tắt bị cắt cụt, không biết câu nào đã được xử lý). Bản tin DCC **không sinh văn bản bằng LLM**: mọi con số đếm
trực tiếp từ dữ liệu vận hành nên không thể bịa.

Nội dung trong một cửa sổ thời gian:
    * Lượt hỏi theo quyết định (FOUND / CONFLICT / CLARIFY / NOT_FOUND / OUT_OF_SCOPE / ERROR).
    * Cụm câu hỏi đang mở, nhiều lượt hỏi nhất trước — việc TA nên xử lý.
    * Cụm đã đóng, đề xuất nguồn đang chờ duyệt, mục nguồn mới/bị thay thế.
    * Phản hồi 👍/👎 và lý do 👎 phổ biến.
"""
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from . import config, gaps, ingest, registry
from .storage import read_jsonl

DECISION_LOG = config.LOG_DIR / "decisions.jsonl"


def _ts(value: str | None) -> datetime | None:
    """Đọc thời điểm ``YYYY-MM-DDTHH:MM:SS`` hoặc ``YYYY-MM-DD HH:MM``; ``None`` nếu không đọc được."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value or "", fmt)
        except ValueError:
            continue
    return None


def _in_window(value: str | None, since: datetime, until: datetime) -> bool:
    """Thời điểm ``value`` có nằm trong ``[since, until]`` không."""
    moment = _ts(value)
    return moment is not None and since <= moment <= until


def build(hours: int = 24, now: datetime | None = None) -> dict[str, Any]:
    """Tổng hợp số liệu bản tin.

    Args:
        hours: Độ dài cửa sổ nhìn lại.
        now: Thời điểm tính (mặc định ``config.now()``).

    Returns:
        ``window``, ``asked``, ``decisions``, ``open_gap_total``, ``open_gaps`` (top 5), ``resolved_gaps``,
        ``pending_proposals``, ``new_entries``, ``superseded_entries``, ``feedback``, ``thumbs_down_reasons``.
    """
    until = now or config.now()
    since = until - timedelta(hours=hours)
    asked = [r for r in read_jsonl(DECISION_LOG) if _in_window(r.get("ts"), since, until)
             and not str(r.get("channel", "")).startswith("eval:")]
    all_gaps = gaps.list_gaps(None)
    open_gaps = sorted((g for g in all_gaps if g["status"] == "open"), key=lambda g: -g["count"])
    feedback = [r for r in read_jsonl(gaps.FEEDBACK_FILE) if _in_window(r.get("ts"), since, until)]
    entries = registry.load_entries()
    return {
        "window": f"{since:%d/%m %H:%M} → {until:%d/%m %H:%M}",
        "asked": len(asked),
        "decisions": Counter(r.get("final", {}).get("decision", "ERROR") for r in asked),
        "open_gap_total": len(open_gaps),
        "open_gaps": open_gaps[:5],
        "resolved_gaps": [g for g in all_gaps if g["status"] == "resolved"
                          and _in_window(g.get("resolved_at"), since, until)],
        "pending_proposals": ingest.list_proposals("pending"),
        "new_entries": [e for e in entries if e["id"].startswith(("SRC-", "TA-"))
                        and _in_window(e.get("published"), since, until)],
        "superseded_entries": [e for e in entries if e.get("status") == "superseded"],
        "feedback": Counter(r["label"] for r in feedback),
        "thumbs_down_reasons": Counter(r["detail"] for r in feedback
                                       if r["label"] == "thumbs_down" and r.get("detail")),
    }


def to_markdown(d: dict[str, Any]) -> str:
    """Hiển thị bản tin dạng Markdown (Discord embed description hoặc web)."""
    dec = d["decisions"]
    lines = [f"**Bản tin DCC cho TA** · {d['window']}",
             f"**{d['asked']}** lượt hỏi · ✅ {dec.get('FOUND', 0)} có nguồn · ⚠️ {dec.get('CONFLICT', 0)} mâu thuẫn · "
             f"❓ {dec.get('CLARIFY', 0)} hỏi lại · 🔎 {dec.get('NOT_FOUND', 0)} chưa có nguồn · "
             f"🚫 {dec.get('OUT_OF_SCOPE', 0)} ngoài phạm vi · ⚙️ {dec.get('ERROR', 0)} lỗi",
             "", f"**Cần TA xử lý — {d['open_gap_total']} cụm đang mở**"]
    lines += [f"• `{g['id']}` {g['decision']} · **{g['count']}** lượt · {g['topic'] or g['questions'][0][:60]}"
              for g in d["open_gaps"]] or ["• Không có 🎉"]
    lines += ["", f"**Đề xuất nguồn chờ duyệt: {len(d['pending_proposals'])}**"]
    lines += [f"• `{p['id']}` {p['relation']} · {p['entry']['title'][:70]}" for p in d["pending_proposals"][:5]]
    lines += ["", f"Đã đóng {len(d['resolved_gaps'])} cụm · thêm {len(d['new_entries'])} mục nguồn · "
                  f"{len(d['superseded_entries'])} mục đang bị thay thế",
              f"Phản hồi: 👍 {d['feedback'].get('thumbs_up', 0)} · 👎 {d['feedback'].get('thumbs_down', 0)} · "
              f"✏️ {d['feedback'].get('wrong_item', 0)}"]
    if d["thumbs_down_reasons"]:
        lines.append("Lý do 👎: " + ", ".join(f"{k} ({v})" for k, v in d["thumbs_down_reasons"].most_common(3)))
    lines.append("_Số liệu đếm trực tiếp từ log vận hành, không do AI tóm tắt._")
    return "\n".join(lines)
