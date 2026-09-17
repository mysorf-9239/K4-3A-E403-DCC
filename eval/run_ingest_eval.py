"""Chạy bộ kiểm thử nạp nguồn ``eval/ingest_set.json`` qua ``ingest.propose`` (LLM thật).

Đề xuất trong eval không được lưu vào hàng chờ (channel ``eval:<id>``). Chạy trên sổ gốc: script tạm ẩn thư mục
``codebase/data/runtime`` nếu có để kết quả không phụ thuộc dữ liệu demo.

Chạy từ gốc repo::

    codebase/.venv/bin/python eval/run_ingest_eval.py
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "codebase"))
sys.path.insert(0, str(ROOT / "eval"))

from run_eval import restore_runtime, stash_runtime  # noqa: E402

from dcc import ingest  # noqa: E402
from dcc.config import LLM_MODEL, LLM_PROVIDER  # noqa: E402

EVAL = ROOT / "eval"
PAUSE_SECONDS = 4.5
MD_HEADER = "# Kết quả kiểm thử nạp nguồn\n\nTrace đầy đủ theo `trace_id` trong `codebase/logs/ingest.jsonl`.\n"


def match(spec: dict[str, Any], proposal: dict[str, Any]) -> bool:
    """Một đề xuất có khớp một kỳ vọng không (hạng mục, quan hệ, mã liên quan, lab, mốc giờ, hạn lặp)."""
    e = proposal["entry"]
    if e["item"] != spec["item"] or proposal["relation"] not in spec["relation"]:
        return False
    if spec.get("related") and not set(spec["related"]) <= set(proposal["related_ids"]):
        return False
    if spec.get("labs") and sorted(e.get("labs") or []) != sorted(spec["labs"]):
        return False
    if spec.get("due_at") and spec["due_at"] not in [d["due_at"] for d in e.get("deadlines") or []]:
        return False
    return not (spec.get("recurring") and e.get("recurring_daily_close") != spec["recurring"])


def judge(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
    """Chấm một case theo ``pass_rule``; trả ``(đạt, lý do trượt)``."""
    reasons = []
    props = result["proposals"]
    if result["error"]:
        reasons.append(f"lỗi LLM: {result['error'][:80]}")
    if case["expect_empty"] and props:
        reasons.append(f"tạo {len(props)} đề xuất cho thông báo không liên quan")
    for spec in case["expect"]:
        if not spec.get("optional") and not any(match(spec, p) for p in props):
            reasons.append(f"thiếu {spec['item']} {spec['relation']}")
    for p in props:
        for d in p["entry"].get("deadlines") or []:
            if any(d["due_at"].startswith(f) for f in case["forbid_due"]):
                reasons.append(f"mốc cấm {d['due_at']}")
    return not reasons, reasons


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    """Chạy một thông báo qua ``ingest.propose`` và chấm."""
    result = ingest.propose(case["text"], case["origin"], None, case["published"], f"eval:{case['id']}")
    ok, reasons = judge(case, result)
    got = [{"item": p["entry"]["item"], "relation": p["relation"], "related": p["related_ids"],
            "labs": p["entry"].get("labs"), "deadlines": p["entry"].get("deadlines"),
            "recurring": p["entry"].get("recurring_daily_close"), "guards": p["guards"]} for p in result["proposals"]]
    return {"id": case["id"], "group": case["group"], "origin": case["origin"], "pass": ok, "fail_reasons": reasons,
            "trace_id": result["trace_id"], "injection": result["injection_detected"], "got": got}


def _table_row(r: dict[str, Any]) -> str:
    """Một dòng bảng Markdown cho kết quả case."""
    got = "<br>".join(f"{g['item']} · {g['relation']} · {','.join(g['related']) or '—'}" for g in r["got"])
    guards = "; ".join(sorted({x for g in r["got"] for x in g["guards"]})) or "—"
    return (f"| {r['id']} | {r['group']} | {r['origin']} | {got or '(không đề xuất)'} | {guards} | "
            f"{'✅' if r['pass'] else '❌'} | {'; '.join(r['fail_reasons']) or '—'} | `{r['trace_id']}` |")


def _report(rows: list[dict[str, Any]]) -> None:
    """Ghi ``eval/results/ingest_<ts>.json`` và thêm bảng lượt mới lên đầu ``eval/ingest_results.md``."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    passed = sum(r["pass"] for r in rows)
    summary = {"run": ts, "provider": LLM_PROVIDER, "model": LLM_MODEL, "total": len(rows), "passed": passed,
               "pass_rate": round(100 * passed / len(rows), 1) if rows else 0}
    (EVAL / "results").mkdir(exist_ok=True)
    (EVAL / "results" / f"ingest_{ts}.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    md = EVAL / "ingest_results.md"
    old = md.read_text(encoding="utf-8")[len(MD_HEADER):] if md.exists() else ""
    lines = [f"\n## Lượt {ts} · {LLM_PROVIDER} · {LLM_MODEL}\n",
             f"**Đạt {passed}/{len(rows)} = {summary['pass_rate']}%**\n",
             "| Case | Nhóm | Nguồn văn bản | Đề xuất AI (hạng mục · quan hệ · liên quan) | Guard | Đạt | Lý do trượt "
             "| trace |", "|---|---|---|---|---|---|---|---|"]
    md.write_text(MD_HEADER + "\n".join(lines + [_table_row(r) for r in rows]) + "\n" + old, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


def main() -> None:
    """Chạy toàn bộ bộ nạp nguồn trên sổ gốc rồi ghi báo cáo."""
    cases = json.loads((EVAL / "ingest_set.json").read_text(encoding="utf-8"))["cases"]
    stash = stash_runtime()
    rows = []
    try:
        for case in cases:
            rows.append(_run_case(case))
            got = [(g["item"], g["relation"], g["related"]) for g in rows[-1]["got"]]
            print(f"{case['id']} {'PASS' if rows[-1]['pass'] else 'FAIL'} {got} {rows[-1]['fail_reasons']}")
            time.sleep(PAUSE_SECONDS)
    finally:
        restore_runtime(stash)
    _report(rows)


if __name__ == "__main__":
    main()
