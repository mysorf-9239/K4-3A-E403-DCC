# codebase — Trợ lý Nộp Bài (nhóm DCC)

| Thư mục / file | Nội dung | Trạng thái |
|---|---|---|
| `mock/index.html` | Prototype bấm được (CP2): giao diện chat giả lập Discord, đủ 4 nhánh FOUND / CLARIFY / NOT_FOUND / correction + nhánh ngoài phạm vi | **Mock** — quyết định bằng luật từ khoá trong JS, chưa gọi AI |
| `data/announcements.json` | 5 thông báo nộp bài **giả lập do nhóm tự soạn** (daily standup ×2 có bản cập nhật, lab 1–4, đề tài, mentor duty) | Fixture — không phải thông báo thật, không copy data pack |
| `flow.md` | Sơ đồ luồng người dùng và điểm quyết định AI | Tài liệu |
| `logs/` *(CP3)* | Trace prompt + raw response của lời gọi LLM thật | Chưa có |

## Chạy mock

**Xem online (không cần tải):** https://htmlpreview.github.io/?https://github.com/mysorf-9239/K4-3A-E403-DCC/blob/main/codebase/mock/index.html

Mở trực tiếp `mock/index.html` bằng trình duyệt (không cần server). Bấm các nút "Kịch bản demo" bên phải hoặc tự gõ câu hỏi. Khung "Quyết định (trace giả lập)" hiện JSON quyết định của từng lượt.

> Dữ liệu trong `mock/index.html` được nhúng từ `data/announcements.json`. Sửa JSON thì nhúng lại để mock đồng bộ.

## Hợp đồng đầu ra của quyết định trung tâm

Ở CP3, hàm `decide()` trong mock được thay bằng lời gọi LLM thật trả về đúng schema này:

```json
{
  "decision": "FOUND | CLARIFY | NOT_FOUND | OUT_OF_SCOPE",
  "item": "daily_standup | lab | de_tai | mentor_duty | null",
  "lab": 2,
  "source_id": "TB-02",
  "superseded": ["TB-01"],
  "missing": "item | lab",
  "reason": "giải thích ngắn"
}
```

Quy tắc: chỉ trả `FOUND` khi có `source_id` thuộc `announcements.json`; các trường nơi nộp / cách nộp / hạn nộp hiển thị **lấy từ nguồn**, không để model tự viết; nhiều nguồn cùng hạng mục thì dùng bản `published` mới nhất và báo bản bị thay thế.

## Mock vs thật

| Thành phần | CP2 | CP3 (dự kiến) |
|---|---|---|
| Giao diện chat | Mock HTML | Giữ nguyên, gọi API backend |
| Quyết định chọn nguồn / hỏi lại / từ chối | Luật từ khoá (mock) | **LLM thật** + trace log |
| Kho thông báo | JSON giả lập | JSON giả lập (giữ nguyên) |
| Kết nối Discord | Giả lập giao diện | Giả lập (non-goal) |
