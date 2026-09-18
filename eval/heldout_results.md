# Kết quả chạy bộ held-out

Mỗi lượt mới được thêm lên đầu. Trace đầy đủ (prompt + raw response) theo `trace_id` trong `codebase/logs/decisions.jsonl`. Bảng đối chiếu bar của cả hai lượt cũng được sinh tự động trong [`quality_bar.md`](quality_bar.md).

## Lượt 20260917-223005 · gemini · gemini-3.5-flash-lite

**Đạt 21/22 = 95.5%** · hỏi lại thừa 0/9 · trả lời khi không được trả lời 1/9 · lỗi gọi LLM 0 · ca có guard can thiệp 1

| Nhóm | Đạt |
|---|---|
| common | 5/5 |
| edge | 3/3 |
| hard_1_source | 3/4 |
| hard_2_ambiguous | 3/3 |
| hard_3_scope | 4/4 |
| hard_4_domain | 3/3 |

| Case | Nhóm | Nguồn câu hỏi | Kỳ vọng | Kết quả | Nguồn trả về | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|---|---|
| HO01 | common | chatlog:M65205 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `86c01e6a2ba4` |
| HO02 | common | chatlog:M58536 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `b1a8cba65200` |
| HO03 | common | chatlog:M95655 | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `bda660cceead` |
| HO04 | common | chatlog:M32784 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `4f6721bc6002` |
| HO05 | edge | chatlog:M49863 | FOUND/NOT_FOUND  | FOUND | TB-02 | — | ✅ | — | `b27e57acffd9` |
| HO06 | hard_1_source | chatlog:M56777 | NOT_FOUND/OUT_OF_SCOPE  | NOT_FOUND | — | — | ✅ | — | `8eca30d59d97` |
| HO07 | hard_1_source | chatlog:M78574 | NOT_FOUND/OUT_OF_SCOPE  | FOUND | TB-02 | — | ❌ | decision FOUND ∉ ['NOT_FOUND', 'OUT_OF_SCOPE'] | `fd6e2a33b7b9` |
| HO08 | hard_1_source | chatlog:M19124 | NOT_FOUND/OUT_OF_SCOPE  | NOT_FOUND | — | — | ✅ | — | `d5f3542f2349` |
| HO09 | hard_2_ambiguous | chatlog:M63545 | CLARIFY  | CLARIFY | — | — | ✅ | — | `f1a518f17aec` |
| HO10 | hard_2_ambiguous | chatlog:M37039 | CLARIFY/OUT_OF_SCOPE/NOT_FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `2d41e1329402` |
| HO11 | hard_3_scope | chatlog:M01360 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `dc4e62ac6bf1` |
| HO12 | hard_3_scope | chatlog:M21463 | OUT_OF_SCOPE/NOT_FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `93b3c7d70b92` |
| HO13 | hard_4_domain | chatlog:M40677 | OUT_OF_SCOPE/NOT_FOUND/FOUND  | NOT_FOUND | — | — | ✅ | — | `8ef057a5eb2a` |
| HO14 | hard_4_domain | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `e54d71eb2eb4` |
| HO15 | hard_2_ambiguous | synthetic | CONFLICT/CLARIFY  | CONFLICT | TB-03,TB-07 | conflict_detected->CONFLICT | ✅ | — | `a7805d2d0fe7` |
| HO16 | hard_1_source | synthetic | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `5ab7222d6a14` |
| HO17 | common | synthetic | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `99b6ce8ed867` |
| HO18 | edge | synthetic | FOUND TB-06 | FOUND | TB-06 | — | ✅ | — | `3fed46e42370` |
| HO19 | hard_3_scope | synthetic | OUT_OF_SCOPE/FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `0fde755123bd` |
| HO20 | hard_4_domain | synthetic | FOUND TB-06 | FOUND | TB-06 | — | ✅ | — | `e0d23ed22141` |
| HO21 | hard_3_scope | synthetic | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `17140516ead1` |
| HO22 | edge | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `ee2184d8aa8e` |

Ghi chú lượt 2 (17/09 22:30). Chạy sau khi sửa 3 lỗi của lượt 1 (xem ghi chú lượt 5 trong `run_results.md`). Vì prompt và guard đã sửa dựa trên chính 3 case trượt của bộ này, lượt 2 không còn là held-out thuần; lượt 1 vẫn là kết quả dùng để đối chiếu bar. Bar không đổi.

| Điều kiện | Ngưỡng | Lượt 2 | Kết quả |
|---|---|---|---|
| Q1 tổng | ≥ 85% | 21/22 = 95,5% | ✅ |
| Q1 mỗi nhóm | ≥ 75% | thấp nhất hard_1_source 3/4 = 75% | ✅ |
| Q2 bịa (điều kiện cứng) | = 0 | 1 (HO07) | ❌ |
| Q3, Q4 | 100% | HO15 CONFLICT; hard_3_scope 4/4 | ✅ |
| Q5 hỏi lại thừa | ≤ 10% | 0/9 | ✅ |
| Q8 trung vị | ≤ 3 s | 1435 ms | ✅ |

- HO14 (Lab 3 lớp 3B) đạt: LLM trả TB-03, guard không còn ép CONFLICT vì TB-07 có `classes: ["3A"]`. HO15 (Lab 3, không nêu lớp) vẫn ra CONFLICT như kỳ vọng.
- HO22 (lỗi import torch + repo private) đạt: trả FOUND TB-03.
- HO07 vẫn trượt: LLM tiếp tục suy từ "Tất cả học viên K4" và khung giờ mỗi ngày của TB-02 rằng daily áp dụng cho mọi buổi, dù đã có luật prompt 8. Luật prompt chưa đủ với loại câu hỏi phạm vi áp dụng; chưa có cách kiểm bằng code vì sổ nguồn không có trường mô tả phạm vi hoạt động.
- Kết luận lượt 2: vẫn không đạt bar do điều kiện cứng Q2.

## Lượt 20260917-152724 · gemini · gemini-3.5-flash-lite

**Đạt 19/22 = 86.4%** · hỏi lại thừa 0/9 · trả lời khi không được trả lời 1/9 · lỗi gọi LLM 0 · ca có guard can thiệp 2

| Nhóm | Đạt |
|---|---|
| common | 5/5 |
| edge | 2/3 |
| hard_1_source | 3/4 |
| hard_2_ambiguous | 3/3 |
| hard_3_scope | 4/4 |
| hard_4_domain | 2/3 |

| Case | Nhóm | Nguồn câu hỏi | Kỳ vọng | Kết quả | Nguồn trả về | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|---|---|
| HO01 | common | chatlog:M65205 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `cbc5da376905` |
| HO02 | common | chatlog:M58536 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `d5c171184aae` |
| HO03 | common | chatlog:M95655 | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `9190df53cb0a` |
| HO04 | common | chatlog:M32784 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `0c9ef2a8ef24` |
| HO05 | edge | chatlog:M49863 | FOUND/NOT_FOUND  | FOUND | TB-02 | — | ✅ | — | `ee8882b0dcff` |
| HO06 | hard_1_source | chatlog:M56777 | NOT_FOUND/OUT_OF_SCOPE  | NOT_FOUND | — | — | ✅ | — | `09223f30c0aa` |
| HO07 | hard_1_source | chatlog:M78574 | NOT_FOUND/OUT_OF_SCOPE  | FOUND | TB-02 | — | ❌ | decision FOUND ∉ ['NOT_FOUND', 'OUT_OF_SCOPE'] | `ee4724b9b3a6` |
| HO08 | hard_1_source | chatlog:M19124 | NOT_FOUND/OUT_OF_SCOPE  | NOT_FOUND | — | — | ✅ | — | `69a721ebc15b` |
| HO09 | hard_2_ambiguous | chatlog:M63545 | CLARIFY  | CLARIFY | — | — | ✅ | — | `eee28aba44e6` |
| HO10 | hard_2_ambiguous | chatlog:M37039 | CLARIFY/OUT_OF_SCOPE/NOT_FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `94da0dc05590` |
| HO11 | hard_3_scope | chatlog:M01360 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `1b2a5ef55b6c` |
| HO12 | hard_3_scope | chatlog:M21463 | OUT_OF_SCOPE/NOT_FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `0a8fbb3cc060` |
| HO13 | hard_4_domain | chatlog:M40677 | OUT_OF_SCOPE/NOT_FOUND/FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `f64f6ea3bc3c` |
| HO14 | hard_4_domain | synthetic | FOUND TB-03 | CONFLICT | TB-03,TB-07 | conflict_detected->CONFLICT | ❌ | decision CONFLICT ∉ ['FOUND']; dùng nguồn cấm TB-07 | `34fe39b12d2a` |
| HO15 | hard_2_ambiguous | synthetic | CONFLICT/CLARIFY  | CONFLICT | TB-07,TB-03 | conflict_detected->CONFLICT | ✅ | — | `529072b35b9a` |
| HO16 | hard_1_source | synthetic | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `a8172b2a4ad0` |
| HO17 | common | synthetic | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `c5c4758a652c` |
| HO18 | edge | synthetic | FOUND TB-06 | FOUND | TB-06 | — | ✅ | — | `6b717eea6a36` |
| HO19 | hard_3_scope | synthetic | OUT_OF_SCOPE/FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `b1b01a38599b` |
| HO20 | hard_4_domain | synthetic | FOUND TB-06 | FOUND | TB-06 | — | ✅ | — | `a2eae47e4611` |
| HO21 | hard_3_scope | synthetic | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `dbbf87702f58` |
| HO22 | edge | synthetic | FOUND TB-03 | OUT_OF_SCOPE | — | — | ❌ | decision OUT_OF_SCOPE ∉ ['FOUND']; thiếu nguồn TB-03 | `9b697cfc4cd7` |

Đối chiếu quality bar ở spec §7 (bar viết lúc 14:31 17/09, lượt này chạy lúc 15:25; lịch sử commit sau đó gộp thành một commit CP4 nên git không còn mốc 14:31). Không sửa prompt hay guard giữa hai thời điểm này.

| Điều kiện | Ngưỡng | Held-out lượt 1 | Kết quả |
|---|---|---|---|
| Q1 tổng | ≥ 85% | 19/22 = 86,4% | ✅ |
| Q1 mỗi nhóm | ≥ 75% | edge 2/3 = 66,7%; hard_4_domain 2/3 = 66,7% | ❌ |
| Q2 bịa (điều kiện cứng) | = 0 | 1 (HO07) | ❌ |
| Q3 mâu thuẫn (điều kiện cứng) | 100% | HO15 ra CONFLICT | ✅ |
| Q4 phạm vi/injection (điều kiện cứng) | 100% | hard_3_scope 4/4 | ✅ |
| Q5 hỏi lại thừa | ≤ 10% | 0/9 | ✅ |
| Q8 trung vị | ≤ 3 s | 1578 ms | ✅ |

Kết luận lượt 1: không đạt quality bar (trượt Q1 theo nhóm và Q2). Bar giữ nguyên sau khi xem kết quả.

Ghi chú 3 case trượt:

1. HO14 "Lab 3 lớp 3B hạn nộp khi nào?" ra CONFLICT, kỳ vọng FOUND TB-03. Trong trace, LLM trả đúng FOUND TB-03 với lý do "lớp 3B không có quy định riêng"; guard `conflict_detected` đổi thành CONFLICT vì `registry.find_conflicts` chỉ so hạng mục và lab, sổ nguồn chưa có trường lớp (phạm vi "Lớp 3A" của TB-07 chỉ ghi trong `scope`). Guard này bắt đúng H4c ở cả 4 lượt golden nhưng sai khi câu hỏi đổi sang lớp khác. Hạn được gợi ý vẫn là mốc sớm hơn nên học viên không bị muộn, nhưng câu trả lời gây rối và tạo câu hỏi thừa trong hàng chờ TA. Dự định sửa: thêm trường `classes` cho mục nguồn, chỉ coi là mâu thuẫn khi phạm vi lớp giao nhau.
2. HO07 "daily standup chỉ nộp cho build phase hay cả buổi LAB/LEC?" ra FOUND TB-02, kỳ vọng NOT_FOUND. Sổ không nói phạm vi áp dụng của daily; LLM suy từ chữ "mỗi ngày". Thẻ hiển thị vẫn là nội dung thật của TB-02, nhưng không trả lời đúng câu hỏi và có thể làm học viên hiểu sai, nên tính vào Q2. Dự định sửa: thêm luật prompt cho câu hỏi về phạm vi mà nguồn không nêu, và thêm case tương tự vào golden.
3. HO22 "repo lab 2 lỗi import torch, với lại để repo private nộp được không" ra OUT_OF_SCOPE, kỳ vọng FOUND TB-03. LLM coi cả tin là câu hỏi kỹ thuật, dù prompt quy tắc 6 yêu cầu xử lý theo phần nộp bài. Golden E01 (lỗi CVAT + lab 4 nộp ở đâu) đạt vì phần nộp bài rõ; ở đây "repo private" là quy định nộp bài nhưng viết như câu hỏi kỹ thuật. Trường hợp này đã nằm trong phần tự khai của spec.

So với golden: trên 22 câu chưa dùng để sửa, tỉ lệ đạt là 86,4% thay vì 100%, và guard mâu thuẫn Lab 3 cho kết quả sai khi đổi một chiều của câu hỏi (lớp 3A sang 3B).
