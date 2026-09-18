"""Tính quality bar Q1–Q8 (chốt trong spec.md §7) cho mọi lượt eval đã chạy.

Chỉ đọc kết quả có sẵn: ``eval/results/run_*.json`` (golden set), ``eval/results/heldout_*.json`` (bộ held-out),
``eval/results/ingest_*.json`` (nạp nguồn) và ``codebase/logs/decisions.jsonl`` (độ trễ theo ``trace_id``).
Không gọi LLM.

Chạy từ gốc repo::

    python3 eval/quality_bar.py        # ghi eval/quality_bar.md
"""
import json
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"
REGISTRY = json.loads((ROOT / "codebase" / "data" / "registry.json").read_text(encoding="utf-8"))
ITEM_OF = {e["id"]: e["item"] for e in REGISTRY["entries"]}
GOLDEN = {c["id"]: c for c in json.loads((EVAL / "golden_set.json").read_text(encoding="utf-8"))["cases"]}
HELDOUT = {c["id"]: c for c in json.loads((EVAL / "heldout_set.json").read_text(encoding="utf-8"))["cases"]}

#: Ngưỡng đã chốt trong spec.md §7 (không sửa sau 21:00 17/09/2026).
BAR = {"Q1_total": 85.0, "Q1_group": 75.0, "Q2_max": 0, "Q3": 100.0, "Q4": 100.0, "Q5_max": 10.0,
       "Q6": 80.0, "Q8_ms": 3000}


def _pct(part: int, whole: int) -> float:
    """Phần trăm làm tròn 1 chữ số; 100 nếu mẫu rỗng."""
    return round(100 * part / whole, 1) if whole else 100.0


def _latencies() -> dict[str, int]:
    """``trace_id`` → ``latency_ms`` từ log quyết định."""
    path = ROOT / "codebase" / "logs" / "decisions.jsonl"
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("latency_ms"):
            out[row["trace_id"]] = row["latency_ms"]
    return out


def _fabricated(row: dict[str, Any], cases: dict[str, Any]) -> bool:
    """Q2: trả FOUND khi không được trả lời, hoặc FOUND có nguồn không tồn tại / sai hạng mục của case."""
    case = cases[row["id"]]
    if row["got"] == "FOUND" and not {"FOUND", "CONFLICT"} & set(case["accept"]):
        return True
    if row["got"] != "FOUND":
        return False
    listed = (case.get("expected_source_ids") or []) + (case.get("if_found_sources") or [])
    expected_items = {ITEM_OF[s] for s in listed}
    return any(s not in ITEM_OF or (expected_items and ITEM_OF[s] not in expected_items) for s in row["got_sources"])


def golden_metrics(run: dict[str, Any], latency: dict[str, int],
                   cases: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tính Q1–Q5, Q8 cho một lượt chạy (golden set, hoặc bộ held-out khi truyền ``cases``)."""
    cases = GOLDEN if cases is None else cases
    rows = run["rows"]
    groups: dict[str, list[bool]] = {}
    for r in rows:
        groups.setdefault(r["group"], []).append(r["pass"])
    conflict_rows = [r for r in rows if cases[r["id"]]["accept"] == ["CONFLICT"]]
    scope_rows = [r for r in rows if r["group"] == "hard_3_scope"]
    found_rows = [r for r in rows if cases[r["id"]]["accept"] == ["FOUND"]]
    lat = [latency[r["trace_id"]] for r in rows if r["trace_id"] in latency]
    return {
        "Q1_total": _pct(sum(r["pass"] for r in rows), len(rows)),
        "Q1_group_min": min(_pct(sum(v), len(v)) for v in groups.values()),
        "Q2": sum(_fabricated(r, cases) for r in rows),
        "Q3": _pct(sum(r["pass"] for r in conflict_rows), len(conflict_rows)),
        "Q4": _pct(sum(r["pass"] for r in scope_rows), len(scope_rows)),
        "Q5": _pct(sum(r["got"] == "CLARIFY" for r in found_rows), len(found_rows)),
        "Q8_ms": int(statistics.median(lat)) if lat else None,
        "errors": sum(r["got"] == "ERROR" for r in rows),
    }


def passes(m: dict[str, Any]) -> dict[str, bool]:
    """So từng chỉ số với ngưỡng."""
    return {"Q1": m["Q1_total"] >= BAR["Q1_total"] and m["Q1_group_min"] >= BAR["Q1_group"],
            "Q2": m["Q2"] <= BAR["Q2_max"], "Q3": m["Q3"] >= BAR["Q3"], "Q4": m["Q4"] >= BAR["Q4"],
            "Q5": m["Q5"] <= BAR["Q5_max"], "Q8": m["Q8_ms"] is not None and m["Q8_ms"] <= BAR["Q8_ms"]}


def _mark(ok: bool) -> str:
    """Ký hiệu đạt/trượt."""
    return "✅" if ok else "❌"


def main() -> None:
    """Tính và ghi ``eval/quality_bar.md``."""
    latency = _latencies()
    lines = ["# Quality bar — kết quả theo từng lượt", "",
             "Sinh tự động bởi `python3 eval/quality_bar.py` từ `eval/results/*.json` và "
             "`codebase/logs/decisions.jsonl`. Ngưỡng chốt trong `spec.md` §7.", "",
             "## Golden set (quyết định trung tâm)", "",
             "| Lượt | Q1 tổng ≥85% | Q1 nhóm thấp nhất ≥75% | Q2 bịa = 0 | Q3 mâu thuẫn 100% | Q4 phạm vi 100% | "
             "Q5 hỏi thừa ≤10% | Q8 trung vị ≤3000ms | Lỗi LLM | Q1–Q4 đạt |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    q14 = []
    for path in sorted((EVAL / "results").glob("run_*.json")):
        m = golden_metrics(json.loads(path.read_text(encoding="utf-8")), latency)
        p = passes(m)
        core = all(p[k] for k in ("Q1", "Q2", "Q3", "Q4"))
        q14.append(core)
        lines.append(f"| {path.stem[4:]} | {m['Q1_total']}% {_mark(m['Q1_total'] >= BAR['Q1_total'])} | "
                     f"{m['Q1_group_min']}% {_mark(m['Q1_group_min'] >= BAR['Q1_group'])} | "
                     f"{m['Q2']} {_mark(p['Q2'])} | "
                     f"{m['Q3']}% {_mark(p['Q3'])} | {m['Q4']}% {_mark(p['Q4'])} | {m['Q5']}% {_mark(p['Q5'])} | "
                     f"{m['Q8_ms']} {_mark(p['Q8'])} | {m['errors']} | {_mark(core)} |")
    lines += ["", f"**Q7 — Q1–Q4 đạt 2 lượt liên tiếp gần nhất:** {_mark(len(q14) >= 2 and all(q14[-2:]))}", "",
              "## Bộ held-out (22 câu chưa dùng để sửa prompt/guard)", "",
              "Bar áp cho bộ này là bar đã chốt, không hạ. Lượt đầu (`20260917-152724`) là lượt duy nhất chạy trước "
              "khi nhóm sửa theo case trượt, nên chỉ lượt đó là held-out thuần.", "",
              "| Lượt | Q1 tổng ≥85% | Q1 nhóm thấp nhất ≥75% | Q2 bịa = 0 | Q3 mâu thuẫn 100% | Q4 phạm vi 100% | "
              "Q5 hỏi thừa ≤10% | Q8 trung vị ≤3000ms | Lỗi LLM | Q1–Q4 đạt |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for path in sorted((EVAL / "results").glob("heldout_*.json")):
        m = golden_metrics(json.loads(path.read_text(encoding="utf-8")), latency, HELDOUT)
        p = passes(m)
        core = all(p[k] for k in ("Q1", "Q2", "Q3", "Q4"))
        lines.append(f"| {path.stem[8:]} | {m['Q1_total']}% {_mark(m['Q1_total'] >= BAR['Q1_total'])} | "
                     f"{m['Q1_group_min']}% {_mark(m['Q1_group_min'] >= BAR['Q1_group'])} | "
                     f"{m['Q2']} {_mark(p['Q2'])} | "
                     f"{m['Q3']}% {_mark(p['Q3'])} | {m['Q4']}% {_mark(p['Q4'])} | {m['Q5']}% {_mark(p['Q5'])} | "
                     f"{m['Q8_ms']} {_mark(p['Q8'])} | {m['errors']} | {_mark(core)} |")
    lines += ["", "## Nạp nguồn (Q6 ≥80%)", "", "| Lượt | Đạt | Q6 |", "|---|---|---|"]
    for path in sorted((EVAL / "results").glob("ingest_*.json")):
        s = json.loads(path.read_text(encoding="utf-8"))["summary"]
        lines.append(f"| {path.stem[7:]} | {s['passed']}/{s['total']} = {s['pass_rate']}% | "
                     f"{_mark(s['pass_rate'] >= BAR['Q6'])} |")
    lines += ["", "Q6 điều kiện cứng \"0 mục vào sổ không qua TA duyệt\" được bảo đảm bằng thiết kế "
              "(`ingest.propose` chỉ tạo đề xuất; chỉ `ingest.approve` ghi sổ) và test "
              "`test_update_proposal_then_edit_and_approve`, "
              "`test_reject_and_eval_channel_not_stored`.", ""]
    (EVAL / "quality_bar.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
