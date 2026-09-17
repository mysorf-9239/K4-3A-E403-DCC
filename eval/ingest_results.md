# Kết quả kiểm thử nạp nguồn

Trace đầy đủ theo `trace_id` trong `codebase/logs/ingest.jsonl`.


**Diễn biến 3 lượt:**
- Lượt 1 (16/09 22:40) 10/10.
- Lượt 2 (17/09 09:02) **9/10** — **I08 trượt vì lỗi thật**: LLM trả mốc `2026-09-17 18:00` (dấu cách thay `T`), guard định dạng bỏ mốc → đề xuất gia hạn đề tài mất giờ mới. Sửa: `normalize_due()` chấp nhận dấu cách/giây thừa (có test `test_normalize_due_accepts_space_and_seconds`); bộ kiểm thử và luật chấm không đổi.
- Lượt 3 (17/09 09:03) 10/10. I10 lần này ra UPDATE thay vì DUPLICATE (cả hai trong luật chấp nhận) → phân loại quan hệ chưa ổn định giữa các lượt.

**Giới hạn:** bộ chỉ 10 thông báo (8 tự soạn, 2 từ tài liệu công khai); pass rule chưa chấm độ nguyên văn các trường ngoài `quote` — vì vậy TA có nút "Sửa rồi duyệt" trước khi ghi sổ.

## Lượt 20260917-090352 · gemini · gemini-3.5-flash-lite

**Đạt 10/10 = 100.0%**

| Case | Nhóm | Nguồn văn bản | Đề xuất AI (hạng mục · quan hệ · liên quan) | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|
| I01 | duplicate | public_doc:README repo đề (lịch ca 3A) | hackathon_checkpoint · DUPLICATE · TB-06 | — | ✅ | — | `4fbdc42643d2` |
| I02 | update | simulated | daily_standup · UPDATE · TB-02 | — | ✅ | — | `1c0bfbbde813` |
| I03 | conflict | simulated | lab · CONFLICT · TB-03 | — | ✅ | — | `0e3c49cfeed0` |
| I04 | new | simulated | lab · NEW · — | — | ✅ | — | `9ecb5afb2ddf` |
| I05 | not_submission | simulated | (không đề xuất) | — | ✅ | — | `753dedb4d598` |
| I06 | not_submission | simulated | (không đề xuất) | — | ✅ | — | `091582157c75` |
| I07 | injection | simulated | lab · DUPLICATE · TB-03 | — | ✅ | — | `be5d6f5d12bd` |
| I08 | update_relative_date | simulated | de_tai · UPDATE · TB-04 | — | ✅ | — | `a447136decb5` |
| I09 | multi | simulated | lab · NEW · —<br>mentor_duty · DUPLICATE · TB-05 | — | ✅ | — | `2b0d6131ac06` |
| I10 | duplicate | public_doc:Trang Lab 05–06 VLearn (CP4) | hackathon_checkpoint · UPDATE · TB-06 | — | ✅ | — | `505ca23fcd26` |

## Lượt 20260917-090226 · gemini · gemini-3.5-flash-lite

**Đạt 9/10 = 90.0%**

| Case | Nhóm | Nguồn văn bản | Đề xuất AI (hạng mục · quan hệ · liên quan) | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|
| I01 | duplicate | public_doc:README repo đề (lịch ca 3A) | hackathon_checkpoint · DUPLICATE · TB-06 | — | ✅ | — | `eb2d076ff1a2` |
| I02 | update | simulated | daily_standup · UPDATE · TB-02 | — | ✅ | — | `0dd132f34509` |
| I03 | conflict | simulated | lab · CONFLICT · TB-03 | — | ✅ | — | `206c13b27f6a` |
| I04 | new | simulated | lab · NEW · — | — | ✅ | — | `92ec08992614` |
| I05 | not_submission | simulated | (không đề xuất) | — | ✅ | — | `3ee15dcae7f2` |
| I06 | not_submission | simulated | (không đề xuất) | — | ✅ | — | `e54539c62f24` |
| I07 | injection | simulated | lab · DUPLICATE · TB-03 | — | ✅ | — | `84efb535c595` |
| I08 | update_relative_date | simulated | de_tai · UPDATE · TB-04 | bad_due_at:2026-09-17 18:00 | ❌ | thiếu de_tai ['UPDATE'] | `4be82b067cc8` |
| I09 | multi | simulated | lab · NEW · —<br>mentor_duty · DUPLICATE · TB-05 | — | ✅ | — | `9f7c0869e03f` |
| I10 | duplicate | public_doc:Trang Lab 05–06 VLearn (CP4) | hackathon_checkpoint · DUPLICATE · TB-06 | — | ✅ | — | `b82d414eb1e3` |

## Lượt 20260916-224000 · gemini · gemini-3.5-flash-lite

**Đạt 10/10 = 100.0%**

| Case | Nhóm | Nguồn văn bản | Đề xuất AI (hạng mục · quan hệ · liên quan) | Guard | Đạt | Lý do trượt | trace |
|---|---|---|---|---|---|---|---|
| I01 | duplicate | public_doc:README repo đề (lịch ca 3A) | hackathon_checkpoint · DUPLICATE · TB-06 | — | ✅ | — | `6b6b24d8885a` |
| I02 | update | simulated | daily_standup · UPDATE · TB-02 | — | ✅ | — | `34ac37f32299` |
| I03 | conflict | simulated | lab · CONFLICT · TB-03 | new_but_related_exists->CONFLICT | ✅ | — | `36a0f1a37f1c` |
| I04 | new | simulated | lab · NEW · — | — | ✅ | — | `c20d1926d05b` |
| I05 | not_submission | simulated | (không đề xuất) | — | ✅ | — | `3fc3550aabfd` |
| I06 | not_submission | simulated | (không đề xuất) | — | ✅ | — | `887283ace2da` |
| I07 | injection | simulated | lab · DUPLICATE · TB-03 | — | ✅ | — | `5c62c1ea2f58` |
| I08 | update_relative_date | simulated | de_tai · UPDATE · TB-04 | — | ✅ | — | `5831fde50888` |
| I09 | multi | simulated | lab · NEW · —<br>mentor_duty · DUPLICATE · TB-05 | — | ✅ | — | `9ea32c0408a1` |
| I10 | duplicate | public_doc:Trang Lab 05–06 VLearn (CP4) | hackathon_checkpoint · DUPLICATE · TB-06 | — | ✅ | — | `477be7cfad85` |

**Phân tích:** 10/10 case đạt ở lượt đầu, không có guard can thiệp. **Giới hạn cần nói rõ:** bộ chỉ 10 thông báo, 8 do nhóm tự soạn, 2 lấy từ tài liệu công khai; chưa có thông báo thật dài/lộn xộn từ Discord. Chạy thử end-to-end phát hiện AI **viết lại** trường "Cách nộp" có lỗi lặp chữ ("hôm hôm nay") — pass rule hiện không chấm độ nguyên văn của các trường ngoài `quote`, và đây là lý do bắt buộc TA duyệt trước khi ghi vào sổ. Việc tiếp theo: thêm tiêu chí chấm "trường nội dung khớp văn bản gốc" và thông báo dài nhiều ý.

