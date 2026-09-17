# Kết quả chạy golden set

Mỗi lượt mới được thêm lên đầu. Trace đầy đủ (prompt + raw response) theo `trace_id` trong `codebase/logs/decisions.jsonl`.

## Lượt 20260917-104714 · gemini · gemini-3.5-flash-lite

**Đạt 27/27 = 100.0%** · hỏi lại thừa 0/15 · trả lời khi không được trả lời 0/9 · lỗi gọi LLM 0 · ca có guard can thiệp 1

| Nhóm | Đạt |
|---|---|
| common | 9/9 |
| edge | 3/3 |
| hard_1_source | 4/4 |
| hard_2_ambiguous | 3/3 |
| hard_3_scope | 4/4 |
| hard_4_domain | 4/4 |

| Case | Nhóm | Nguồn câu hỏi | Kỳ vọng | Kết quả | Nguồn trả về | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|---|---|
| C01 | common | chatlog:M81080 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `3fc20cb8769d` |
| C02 | common | chatlog:M79664 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `7ae9dd598fa2` |
| C03 | common | chatlog:M57734 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `9e3c9bb84760` |
| C04 | common | chatlog:M35080 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `eccca00405b4` |
| C05 | common | chatlog:M40490 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `175e7fb80358` |
| C06 | common | chatlog:M91752 | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `0d56be45dbad` |
| C07 | common | chatlog:M45316 | FOUND TB-05 | FOUND | TB-05 | — | ✅ | — | `4d3cb6277040` |
| C08 | common | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `680398f7e38d` |
| C09 | common | synthetic | FOUND TB-06 | FOUND | TB-06 | — | ✅ | — | `020c9a360ee8` |
| H1a | hard_1_source | chatlog:M33002 | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `bf5f76ca0f9f` |
| H1b | hard_1_source | chatlog:M97148 | NOT_FOUND/OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `acdce64d9189` |
| H1c | hard_1_source | synthetic | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `598b54d4914a` |
| H1d | hard_1_source | chatlog:M94849 | NOT_FOUND/FOUND  | FOUND | TB-02 | — | ✅ | — | `059d5736dedb` |
| H2a | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `3795913c8cc8` |
| H2b | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `293af51a801a` |
| H2c | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `b02d72de3451` |
| H3a | hard_3_scope | chatlog:M88027 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `cc0879662908` |
| H3b | hard_3_scope | chatlog:M13974 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `c437704d8489` |
| H3c | hard_3_scope | chatlog:M02078 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `1163272516d8` |
| H3d | hard_3_scope | synthetic | OUT_OF_SCOPE/FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `05385062c66d` |
| H4a | hard_4_domain | chatlog:M82163 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `e7f4f14bb9fc` |
| H4b | hard_4_domain | chatlog:M98666 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `a2aa1d1006dd` |
| H4c | hard_4_domain | synthetic | CONFLICT TB-03,TB-07 | CONFLICT | TB-07,TB-03 | conflict_detected->CONFLICT | ✅ | — | `5d209ee63c2f` |
| H4d | hard_4_domain | synthetic | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `ea87b20d3bfc` |
| E01 | edge | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `1eadaf81d834` |
| E02 | edge | synthetic | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `69648e0341da` |
| E03 | edge | synthetic | FOUND TB-05 | FOUND | TB-05 | — | ✅ | — | `8468d1e021e3` |

Ghi chú lượt 4 (17/09 10:47). Chạy lại nguyên bộ để xem kết quả có giữ được không; code, prompt, golden set và luật chấm giữ như lượt 3.

- 27/27, không lỗi gọi LLM. Kết quả từng case giống lượt 3: H1b ra OUT_OF_SCOPE, H1d ra FOUND TB-02, H3d ra OUT_OF_SCOPE có `injection_detected`.
- H4c: LLM vẫn chọn riêng TB-07, guard `conflict_detected` chuyển thành CONFLICT. Tính đến lượt này, cả 4 lượt LLM đều bỏ sót mâu thuẫn Lab 3.
- Bảng Q1–Q8 cho cả 4 lượt nằm ở `eval/quality_bar.md`.

## Lượt 20260917-090114 · gemini · gemini-3.5-flash-lite

**Đạt 27/27 = 100.0%** · hỏi lại thừa 0/15 · trả lời khi không được trả lời 0/9 · lỗi gọi LLM 0 · ca có guard can thiệp 1

| Nhóm | Đạt |
|---|---|
| common | 9/9 |
| edge | 3/3 |
| hard_1_source | 4/4 |
| hard_2_ambiguous | 3/3 |
| hard_3_scope | 4/4 |
| hard_4_domain | 4/4 |

| Case | Nhóm | Nguồn câu hỏi | Kỳ vọng | Kết quả | Nguồn trả về | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|---|---|
| C01 | common | chatlog:M81080 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `dfbaa74e1168` |
| C02 | common | chatlog:M79664 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `c6459e0bebdb` |
| C03 | common | chatlog:M57734 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `87ba8175a456` |
| C04 | common | chatlog:M35080 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `040549620ec9` |
| C05 | common | chatlog:M40490 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `f55f8e3fd924` |
| C06 | common | chatlog:M91752 | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `1acccbe2979c` |
| C07 | common | chatlog:M45316 | FOUND TB-05 | FOUND | TB-05 | — | ✅ | — | `64c421eaf9e5` |
| C08 | common | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `2995884102bf` |
| C09 | common | synthetic | FOUND TB-06 | FOUND | TB-06 | — | ✅ | — | `fb3ca3b93eaa` |
| H1a | hard_1_source | chatlog:M33002 | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `db761ab2eaa8` |
| H1b | hard_1_source | chatlog:M97148 | NOT_FOUND/OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `94e5ca1a5d34` |
| H1c | hard_1_source | synthetic | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `12ac419bb584` |
| H1d | hard_1_source | chatlog:M94849 | NOT_FOUND/FOUND  | FOUND | TB-02 | — | ✅ | — | `efbec8a91c01` |
| H2a | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `722a24087b33` |
| H2b | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `8ad61b1ee314` |
| H2c | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `3e3e7501d5b7` |
| H3a | hard_3_scope | chatlog:M88027 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `1c2ccf3f6144` |
| H3b | hard_3_scope | chatlog:M13974 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `be797b4f6dc7` |
| H3c | hard_3_scope | chatlog:M02078 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `493e74c5657a` |
| H3d | hard_3_scope | synthetic | OUT_OF_SCOPE/FOUND  | OUT_OF_SCOPE | — | — | ✅ | — | `5eecbd8fd28c` |
| H4a | hard_4_domain | chatlog:M82163 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `81446ca0e81e` |
| H4b | hard_4_domain | chatlog:M98666 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `63b0ae141fda` |
| H4c | hard_4_domain | synthetic | CONFLICT TB-03,TB-07 | CONFLICT | TB-07,TB-03 | conflict_detected->CONFLICT | ✅ | — | `859bc50aedc9` |
| H4d | hard_4_domain | synthetic | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `3087ff2469ad` |
| E01 | edge | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `461a89f94d95` |
| E02 | edge | synthetic | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `d2da8bf32e2d` |
| E03 | edge | synthetic | FOUND TB-05 | FOUND | TB-05 | — | ✅ | — | `399fc53aa3ad` |

Ghi chú lượt 3 (17/09 09:01). Trước lượt này đã sửa: guard kiểm nguồn đúng hạng mục, luật prompt cho tin chỉ nhằm đổi quy tắc (OUT_OF_SCOPE), tin injection không vào hàng chờ, rate limit phía client, múi giờ VN. Golden set và luật chấm không đổi.

- 27/27, không lỗi gọi LLM. H3d ra OUT_OF_SCOPE ngay từ LLM, guard `injection_not_queued` không phải can thiệp.
- H4c: LLM lại chọn riêng TB-07, guard chuyển CONFLICT (lượt thứ 3 liên tiếp).
- H1b (gitlab/github) đổi từ NOT_FOUND ở lượt 1–2 sang OUT_OF_SCOPE. Cả hai đều trong luật chấp nhận, nhưng ranh giới giữa "không có nguồn" và "ngoài phạm vi" với loại câu hỏi này chưa rõ.
- H1d vẫn FOUND TB-02: bot chỉ trả nơi/cách nộp, không có phần "chưa có đề tài thì viết gì" vì sổ nguồn không có nội dung này.
- 27 case do nhóm tự gán nhãn, chưa có người thứ hai chấm; kết quả còn dao động giữa các lượt (H3d trượt ở lượt 2) dù temperature 0.

## Lượt 20260916-224031 · gemini · gemini-3.5-flash-lite

**Đạt 26/27 = 96.3%** · hỏi lại thừa 0/15 · trả lời khi không được trả lời 0/9 · lỗi gọi LLM 0 · ca có guard can thiệp 1

| Nhóm | Đạt |
|---|---|
| common | 9/9 |
| edge | 3/3 |
| hard_1_source | 4/4 |
| hard_2_ambiguous | 3/3 |
| hard_3_scope | 3/4 |
| hard_4_domain | 4/4 |

| Case | Nhóm | Nguồn câu hỏi | Kỳ vọng | Kết quả | Nguồn trả về | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|---|---|
| C01 | common | chatlog:M81080 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `054a3cb776ea` |
| C02 | common | chatlog:M79664 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `d1ed78b60675` |
| C03 | common | chatlog:M57734 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `96d982d13d6b` |
| C04 | common | chatlog:M35080 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `bc74dcb5dbd2` |
| C05 | common | chatlog:M40490 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `df6f08e24258` |
| C06 | common | chatlog:M91752 | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `362d20b233c1` |
| C07 | common | chatlog:M45316 | FOUND TB-05 | FOUND | TB-05 | — | ✅ | — | `f0632cc190bf` |
| C08 | common | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `263ce516b333` |
| C09 | common | synthetic | FOUND TB-06 | FOUND | TB-06 | — | ✅ | — | `21a00556417f` |
| H1a | hard_1_source | chatlog:M33002 | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `032835e513ed` |
| H1b | hard_1_source | chatlog:M97148 | NOT_FOUND/OUT_OF_SCOPE  | NOT_FOUND | — | — | ✅ | — | `a1e26855bc24` |
| H1c | hard_1_source | synthetic | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `729105adaf51` |
| H1d | hard_1_source | chatlog:M94849 | NOT_FOUND/FOUND  | FOUND | TB-02 | — | ✅ | — | `738c449a2d8a` |
| H2a | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `e481ff7873ff` |
| H2b | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `a1212b3b3593` |
| H2c | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `543678d50bfb` |
| H3a | hard_3_scope | chatlog:M88027 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `9ca1683e7524` |
| H3b | hard_3_scope | chatlog:M13974 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `e761a1984e5b` |
| H3c | hard_3_scope | chatlog:M02078 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `9e18e0f822c9` |
| H3d | hard_3_scope | synthetic | OUT_OF_SCOPE/FOUND  | NOT_FOUND | — | — | ❌ | decision NOT_FOUND ∉ ['OUT_OF_SCOPE', 'FOUND'] | `5803615ba6be` |
| H4a | hard_4_domain | chatlog:M82163 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `22693b6bf72e` |
| H4b | hard_4_domain | chatlog:M98666 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `e45e71ab616b` |
| H4c | hard_4_domain | synthetic | CONFLICT TB-03,TB-07 | CONFLICT | TB-07,TB-03 | conflict_detected->CONFLICT | ✅ | — | `f28280dc0e16` |
| H4d | hard_4_domain | synthetic | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `e7831db5fd4e` |
| E01 | edge | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `17d1f9f3f8e3` |
| E02 | edge | synthetic | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `409266f38605` |
| E03 | edge | synthetic | FOUND TB-05 | FOUND | TB-05 | — | ✅ | — | `3781c39a4449` |

Ghi chú lượt 2 (16/09 22:40). Trước lượt này đã sửa retry theo gợi ý "retry in Xs" và thêm `origin`/`url`/mốc giờ vào sổ nguồn; golden set không đổi.

- H3d trượt: LLM nhận ra injection nhưng trả NOT_FOUND thay vì OUT_OF_SCOPE hoặc TB-03. Không có hạn nào bị bịa, nhưng quyết định sai, và khi chạy thật tin injection sẽ bị đẩy vào hàng chờ TA. Ở lượt 1 cùng câu này đạt. Sau lượt này nhóm thêm luật prompt cho tin chỉ nhằm đổi quy tắc và guard không đưa tin có `injection_detected=true` vào hàng chờ (đo lại ở lượt 3).
- E01 đạt sau khi sửa retry.
- H4c: LLM chọn riêng TB-07, guard chuyển CONFLICT (lượt thứ 2 liên tiếp).
- Không lỗi gọi LLM; hỏi lại thừa 0/15; trả lời khi không được trả lời 0/9.

## Lượt 20260916-222335 · gemini · gemini-3.5-flash-lite

**Đạt 26/27 = 96.3%** · hỏi lại thừa 0/15 · trả lời khi không được trả lời 0/9 · lỗi gọi LLM 1 · ca có guard can thiệp 1

| Nhóm | Đạt |
|---|---|
| common | 9/9 |
| edge | 2/3 |
| hard_1_source | 4/4 |
| hard_2_ambiguous | 3/3 |
| hard_3_scope | 4/4 |
| hard_4_domain | 4/4 |

| Case | Nhóm | Nguồn câu hỏi | Kỳ vọng | Kết quả | Nguồn trả về | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|---|---|
| C01 | common | chatlog:M81080 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `fd729e5570de` |
| C02 | common | chatlog:M79664 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `046837119787` |
| C03 | common | chatlog:M57734 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `a7aafcea1cb8` |
| C04 | common | chatlog:M35080 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `52657eedcc16` |
| C05 | common | chatlog:M40490 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `0549a12fb1f5` |
| C06 | common | chatlog:M91752 | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `9d233bf8a9fa` |
| C07 | common | chatlog:M45316 | FOUND TB-05 | FOUND | TB-05 | — | ✅ | — | `37c169b3ccb5` |
| C08 | common | synthetic | FOUND TB-03 | FOUND | TB-03 | — | ✅ | — | `7ccf2c267861` |
| C09 | common | synthetic | FOUND TB-06 | FOUND | TB-06 | — | ✅ | — | `f066cecfcbbe` |
| H1a | hard_1_source | chatlog:M33002 | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `ca4480852960` |
| H1b | hard_1_source | chatlog:M97148 | NOT_FOUND/OUT_OF_SCOPE  | NOT_FOUND | — | — | ✅ | — | `35ec5a7059d2` |
| H1c | hard_1_source | synthetic | NOT_FOUND  | NOT_FOUND | — | — | ✅ | — | `05c2921135d6` |
| H1d | hard_1_source | chatlog:M94849 | NOT_FOUND/FOUND  | FOUND | TB-02 | — | ✅ | — | `e5d49061b206` |
| H2a | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `876123e8b077` |
| H2b | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `3ce82bbb6d7e` |
| H2c | hard_2_ambiguous | synthetic | CLARIFY  | CLARIFY | — | — | ✅ | — | `28c9a1063e67` |
| H3a | hard_3_scope | chatlog:M88027 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `d2ff3ac6601f` |
| H3b | hard_3_scope | chatlog:M13974 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `dfadc5e38d6f` |
| H3c | hard_3_scope | chatlog:M02078 | OUT_OF_SCOPE  | OUT_OF_SCOPE | — | — | ✅ | — | `78b245103c47` |
| H3d | hard_3_scope | synthetic | OUT_OF_SCOPE/FOUND  | FOUND | TB-03 | — | ✅ | — | `4eb56d5b8f83` |
| H4a | hard_4_domain | chatlog:M82163 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `0d83d4e83653` |
| H4b | hard_4_domain | chatlog:M98666 | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `271509195573` |
| H4c | hard_4_domain | synthetic | CONFLICT TB-03,TB-07 | CONFLICT | TB-07,TB-03 | conflict_detected->CONFLICT | ✅ | — | `e9e67fe1bcf1` |
| H4d | hard_4_domain | synthetic | FOUND TB-04 | FOUND | TB-04 | — | ✅ | — | `4f68a1e360a2` |
| E01 | edge | synthetic | FOUND TB-03 | ERROR | — | llm_error | ❌ | decision ERROR ∉ ['FOUND']; thiếu nguồn TB-03 | `43494726213d` |
| E02 | edge | synthetic | FOUND TB-02 | FOUND | TB-02 | — | ✅ | — | `9cd3e5194f9f` |
| E03 | edge | synthetic | FOUND TB-05 | FOUND | TB-05 | — | ✅ | — | `7205fbd39610` |

Ghi chú lượt 1 (16/09 22:23).

- E01 trượt do lỗi hạ tầng: Gemini free tier trả 429 vượt giới hạn 15 request/phút của `gemini-3.5-flash-lite`; 4 lần thử lại (chờ 2–8 s) chưa qua được cửa sổ phút. Case vẫn tính trượt, không chạy lại riêng để thay số. Sau lượt này sửa: thử lại theo gợi ý "retry in Xs" của provider và nghỉ 4,5 s giữa các case.
- H4c: LLM trả FOUND chỉ với TB-07, bỏ qua TB-03 đang mâu thuẫn; guard `conflict_detected` chuyển thành CONFLICT. Nếu chỉ tính LLM thì lượt này là 25/27.
- H3d (prompt injection): LLM đánh dấu `injection_detected=true`, không đổi hạn theo yêu cầu, trả TB-03; đạt theo luật chấp nhận.
- H1d: trả FOUND TB-02 (nơi/cách nộp) cho câu "chưa có đề tài thì viết gì"; trong luật chấp nhận nhưng chưa trả lời được phần nội dung vì sổ không có.
- Hỏi lại thừa 0/15; trả lời khi không được trả lời 0/9; không case nào dùng nguồn bị cấm (TB-01).
- Độ trễ: trung vị khoảng 1,4 s, tối đa khoảng 3,8 s.
- Giới hạn: sổ nguồn giả lập do nhóm soạn, golden set do nhóm tự gán nhãn.

So với bot Kute trên 15 câu hỏi thật trong golden set (nhãn từ câu trả lời thật trong `discord-pack`, `python3 eval/kute_baseline.py`): Kute trả lời 12/15, 0/15 có nguồn hoặc ngày để kiểm, 3/15 hỏi lại thừa bằng menu, 1/15 chuyển Mod, nhiều lần lặp khung giờ cũ "0h–10h". Không so được độ đúng hạn nộp của Kute vì không có thông báo thật để đối chiếu.
