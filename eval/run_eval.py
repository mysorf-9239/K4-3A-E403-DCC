"""Chạy toàn bộ golden set qua quyết định trung tâm (LLM thật) và ghi kết quả.

Chạy từ gốc repo:  codebase/.venv/bin/python eval/run_eval.py [--set heldout] [mã case ...]
Kết quả: eval/results/run_<thời điểm>.json + bảng trong eval/run_results.md (thêm lượt mới lên đầu).
Với ``--set heldout``: đọc eval/heldout_set.json, ghi eval/results/heldout_<thời điểm>.json + eval/heldout_results.md.
"""
import json
import shutil
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "codebase"))

from dcc.config import LLM_MODEL, LLM_PROVIDER, RUNTIME_DIR  # noqa: E402
from dcc.decide import decide  # noqa: E402

EVAL = ROOT / "eval"
SET_NAME = "heldout" if "--set" in sys.argv and sys.argv[sys.argv.index("--set") + 1] == "heldout" else "golden"
GOLDEN = json.loads((EVAL / f"{SET_NAME}_set.json").read_text(encoding="utf-8"))
PREFIX = "heldout" if SET_NAME == "heldout" else "run"
RESULTS_MD = "heldout_results.md" if SET_NAME == "heldout" else "run_results.md"
#: Nghỉ giữa các case để không vượt giới hạn request/phút của free tier (Gemini flash-lite: 15/phút).
PAUSE_SECONDS = 4.5


def judge(case: dict[str, Any], out: dict[str, Any]) -> tuple[bool, list[str]]:
    """Chấm một case theo ``pass_rule`` của golden set.

    Args:
        case: Case trong ``golden_set.json``.
        out: Kết quả ``decide()``.

    Returns:
        tuple[bool, list[str]]: Đạt hay không và các lý do trượt.
    """
    reasons = []
    dec, src = out["decision"], out["source_ids"]
    if dec not in case["accept"]:
        reasons.append(f"decision {dec} ∉ {case['accept']}")
    for s in case["expected_source_ids"]:
        if s not in src:
            reasons.append(f"thiếu nguồn {s}")
    for s in case["forbidden_source_ids"]:
        if s in src:
            reasons.append(f"dùng nguồn cấm {s}")
    if dec == "FOUND" and case.get("if_found_sources") and not set(case["if_found_sources"]) & set(src):
        reasons.append(f"FOUND nhưng nguồn {src} ≠ {case['if_found_sources']}")
    if case.get("expected_missing") and dec == "CLARIFY" and out.get("missing") != case["expected_missing"]:
        reasons.append(f"hỏi lại sai trường {out.get('missing')}")
    return not reasons, reasons


def main() -> None:
    """Chạy golden set (có thể lọc theo mã case trên dòng lệnh), in từng case, ghi JSON và bảng Markdown."""
    only = {a for a in sys.argv[1:] if a not in ("--set", "heldout", "golden")}
    stash = stash_runtime()
    try:
        rows = _run_cases(only)
    finally:
        restore_runtime(stash)
    _report(rows)


def stash_runtime() -> Path | None:
    """Tạm ẩn dữ liệu runtime (mục TA/nạp nguồn khi demo) để eval chạy trên sổ nguồn gốc."""
    if RUNTIME_DIR.exists() and any(RUNTIME_DIR.iterdir()):
        stash = RUNTIME_DIR.with_name("runtime_stash_eval")
        shutil.move(str(RUNTIME_DIR), str(stash))
        RUNTIME_DIR.mkdir()
        return stash
    return None


def restore_runtime(stash: Path | None) -> None:
    """Trả lại dữ liệu runtime đã ẩn."""
    if stash:
        shutil.rmtree(RUNTIME_DIR)
        shutil.move(str(stash), str(RUNTIME_DIR))


def _run_cases(only: set[str]) -> list[dict[str, Any]]:
    """Chạy từng case qua ``decide`` (LLM thật, không cache) và chấm."""
    rows = []
    for case in GOLDEN["cases"]:
        if only and case["id"] not in only:
            continue
        out = decide(case["question"], case.get("hint"), channel=f"eval:{case['id']}", use_cache=False)
        ok, reasons = judge(case, out)
        rows.append({"id": case["id"], "group": case["group"], "origin": case["origin"],
                     "question": case["question"], "expected": case["accept"],
                     "expected_sources": case["expected_source_ids"], "got": out["decision"],
                     "got_sources": out["source_ids"], "missing": out.get("missing"),
                     "guards": out["guards"], "injection": out["injection_detected"],
                     "trace_id": out["trace_id"], "pass": ok, "fail_reasons": reasons, "reason": out["reason"]})
        print(f"{case['id']:4} {'PASS' if ok else 'FAIL'} {out['decision']:12} {out['source_ids']} {reasons}")
        time.sleep(PAUSE_SECONDS)
    return rows


def _summary(rows: list[dict[str, Any]], ts: str) -> dict[str, Any]:
    """Tổng hợp tỷ lệ đạt, theo nhóm, hỏi lại thừa, trả lời khi không được trả lời, lỗi, số ca guard can thiệp."""
    total = len(rows)
    passed = sum(r["pass"] for r in rows)
    by_group: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in rows:
        by_group[r["group"]][0] += r["pass"]
        by_group[r["group"]][1] += 1
    found_expected = [r for r in rows if r["expected"] == ["FOUND"]]
    over_clarify = sum(r["got"] == "CLARIFY" for r in found_expected)
    should_not_answer = [r for r in rows if "FOUND" not in r["expected"] and "CONFLICT" not in r["expected"]]
    fabricated = sum(r["got"] == "FOUND" for r in should_not_answer)
    errors = sum(r["got"] == "ERROR" for r in rows)
    guard_fixes = sum(bool([g for g in r["guards"] if g != "llm_error"]) for r in rows)

    summary = {"run": ts, "provider": LLM_PROVIDER, "model": LLM_MODEL, "total": total, "passed": passed,
               "pass_rate": round(100 * passed / total, 1) if total else 0,
               "by_group": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_group.items())},
               "over_clarify": f"{over_clarify}/{len(found_expected)}",
               "fabricated_answer": f"{fabricated}/{len(should_not_answer)}",
               "llm_errors": errors, "cases_with_guard_fix": guard_fixes,
               "decisions": dict(Counter(r["got"] for r in rows))}
    return summary


def _report(rows: list[dict[str, Any]]) -> None:
    """Ghi ``eval/results/run_<ts>.json``, thêm bảng vào ``eval/run_results.md`` và in tóm tắt."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    summary = _summary(rows, ts)
    (EVAL / "results").mkdir(exist_ok=True)
    (EVAL / "results" / f"{PREFIX}_{ts}.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(summary, rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def write_markdown(s: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    """Thêm bảng kết quả lượt mới lên đầu ``eval/run_results.md`` (giữ các lượt cũ và phần phân tích).

    Args:
        s: Tóm tắt lượt chạy.
        rows: Kết quả từng case.
    """
    md = EVAL / RESULTS_MD
    title = "bộ held-out" if SET_NAME == "heldout" else "golden set"
    header = (f"# Kết quả chạy {title}\n\nMỗi lượt mới được thêm lên đầu. Trace đầy đủ (prompt + raw response) theo "
              "`trace_id` trong `codebase/logs/decisions.jsonl`.\n")
    old = md.read_text(encoding="utf-8") if md.exists() else header
    body = old[len(header):] if old.startswith(header) else old
    lines = [f"\n## Lượt {s['run']} · {s['provider']} · {s['model']}\n",
             f"**Đạt {s['passed']}/{s['total']} = {s['pass_rate']}%** · hỏi lại thừa {s['over_clarify']} · "
             f"trả lời khi không được trả lời {s['fabricated_answer']} · lỗi gọi LLM {s['llm_errors']} · "
             f"ca có guard can thiệp {s['cases_with_guard_fix']}\n",
             "| Nhóm | Đạt |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in s["by_group"].items()]
    lines += ["", "| Case | Nhóm | Nguồn câu hỏi | Kỳ vọng | Kết quả | Nguồn trả về | Guard | Đạt | Lý do trượt "
                  "| trace |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['group']} | {r['origin']} | {'/'.join(r['expected'])} "
                     f"{','.join(r['expected_sources'])} | {r['got']} | {','.join(r['got_sources']) or '—'} | "
                     f"{'; '.join(r['guards']) or '—'} | {'✅' if r['pass'] else '❌'} | "
                     f"{'; '.join(r['fail_reasons']) or '—'} | `{r['trace_id']}` |")
    lines.append("\n**Phân tích nguyên nhân các case trượt:** _(nhóm điền sau khi đọc trace)_\n")
    md.write_text(header + "\n".join(lines) + body, encoding="utf-8")


if __name__ == "__main__":
    main()
