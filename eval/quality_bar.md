# Quality bar — kết quả theo từng lượt

Sinh tự động bởi `python3 eval/quality_bar.py` từ `eval/results/*.json` và `codebase/logs/decisions.jsonl`. Ngưỡng chốt trong `spec.md` §7.

## Golden set (quyết định trung tâm)

| Lượt | Q1 tổng ≥85% | Q1 nhóm thấp nhất ≥75% | Q2 bịa = 0 | Q3 mâu thuẫn 100% | Q4 phạm vi 100% | Q5 hỏi thừa ≤10% | Q8 trung vị ≤3000ms | Lỗi LLM | Q1–Q4 đạt |
|---|---|---|---|---|---|---|---|---|---|
| 20260916-222335 | 96.3% ✅ | 66.7% ❌ | 0 ✅ | 100.0% ✅ | 100.0% ✅ | 0.0% ✅ | 1420 ✅ | 1 | ❌ |
| 20260916-224031 | 96.3% ✅ | 75.0% ✅ | 0 ✅ | 100.0% ✅ | 75.0% ❌ | 0.0% ✅ | 1407 ✅ | 0 | ❌ |
| 20260917-090114 | 100.0% ✅ | 100.0% ✅ | 0 ✅ | 100.0% ✅ | 100.0% ✅ | 0.0% ✅ | 1465 ✅ | 0 | ✅ |
| 20260917-104714 | 100.0% ✅ | 100.0% ✅ | 0 ✅ | 100.0% ✅ | 100.0% ✅ | 0.0% ✅ | 1497 ✅ | 0 | ✅ |
| 20260917-222753 | 100.0% ✅ | 100.0% ✅ | 0 ✅ | 100.0% ✅ | 100.0% ✅ | 0.0% ✅ | 1451 ✅ | 0 | ✅ |

**Q7 — Q1–Q4 đạt 2 lượt liên tiếp gần nhất:** ✅

## Bộ held-out (22 câu chưa dùng để sửa prompt/guard)

Bar áp cho bộ này là bar đã chốt, không hạ. Lượt đầu (`20260917-152724`) là lượt duy nhất chạy trước khi nhóm sửa theo case trượt, nên chỉ lượt đó là held-out thuần.

| Lượt | Q1 tổng ≥85% | Q1 nhóm thấp nhất ≥75% | Q2 bịa = 0 | Q3 mâu thuẫn 100% | Q4 phạm vi 100% | Q5 hỏi thừa ≤10% | Q8 trung vị ≤3000ms | Lỗi LLM | Q1–Q4 đạt |
|---|---|---|---|---|---|---|---|---|---|
| 20260917-152724 | 86.4% ✅ | 66.7% ❌ | 1 ❌ | 100.0% ✅ | 100.0% ✅ | 0.0% ✅ | 1578 ✅ | 0 | ❌ |
| 20260917-223005 | 95.5% ✅ | 75.0% ✅ | 1 ❌ | 100.0% ✅ | 100.0% ✅ | 0.0% ✅ | 1435 ✅ | 0 | ❌ |

## Nạp nguồn (Q6 ≥80%)

| Lượt | Đạt | Q6 |
|---|---|---|
| 20260916-224000 | 10/10 = 100.0% | ✅ |
| 20260917-090226 | 9/10 = 90.0% | ✅ |
| 20260917-090352 | 10/10 = 100.0% | ✅ |

Q6 điều kiện cứng "0 mục vào sổ không qua TA duyệt" được bảo đảm bằng thiết kế (`ingest.propose` chỉ tạo đề xuất; chỉ `ingest.approve` ghi sổ) và test `test_update_proposal_then_edit_and_approve`, `test_reject_and_eval_channel_not_stored`.
