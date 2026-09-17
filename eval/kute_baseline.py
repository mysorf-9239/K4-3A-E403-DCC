"""Tổng hợp baseline bot Kute từ nhãn quan sát trong golden_set.json (câu trả lời thật trong discord-pack)."""
import json
from pathlib import Path

cases = [c for c in json.loads((Path(__file__).parent / "golden_set.json").read_text(encoding="utf-8"))["cases"]
         if "kute_baseline" in c]
n = len(cases)
k = [c["kute_baseline"] for c in cases]
print(f"Số câu hỏi thật có quan sát Kute: {n}")
print(f"Bot có trả lời: {sum(x['replied'] for x in k)}/{n}")
print(f"Trả lời kèm nguồn/ngày kiểm tra được: {sum(x['has_source'] for x in k)}/{n}")
print(f"Hỏi lại thừa (câu đã rõ vẫn hiện menu): {sum(x['over_clarify'] for x in k)}/{n}")
print(f"Chuyển Mod: {sum(x['escalated'] for x in k)}/{n}")
for c in cases:
    print(f"- {c['id']} ({c['origin']}): {c['kute_baseline']['note']}")
