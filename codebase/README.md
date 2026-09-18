# codebase — Bot DCC (nhóm DCC)

Bot **DCC** trả lời **nơi nộp · cách nộp · hạn nộp** cho học viên AI20k **chỉ từ sổ nguồn có phiên bản**, kèm trích dẫn
và link. Khác bot Kute hiện tại ở bốn điểm:

1. **Nguồn sống, không phải FAQ cứng:** thông báo mới (kênh thông báo, chuột phải tin nhắn, `/source-add`) được AI trích
   xuất và phân loại **NEW / UPDATE / CONFLICT / DUPLICATE** so với sổ; TA duyệt một nút là học viên hỏi lại nhận ngay
   quy định mới, bản cũ bị đánh dấu thay thế.
2. **Không tự chọn khi nguồn mâu thuẫn:** trả `CONFLICT`, hiện cả hai nguồn và đưa TA xác nhận.
3. **Câu chưa có nguồn không bị bỏ rơi:** gom cụm vào hàng chờ TA, TA trả lời một lần → thành nguồn cho mọi người sau.
4. **Giúp không quên hạn:** `/deadlines` và nhắc hạn DM **tự đăng ký**; TA có `/ta-digest` đếm số liệu thật (không để
   LLM tóm tắt).

## Nguồn lấy từ đâu

| Loại (`origin`) | Nội dung                                                                                                                                                             | Ở đâu                       |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| `public_doc`    | Tài liệu **công khai** của khoá - hiện có lịch CP1–CP5 ca 3A (README repo đề + trang Lab 05–06 VLearn), kèm `url`                                                    | `data/registry.json`        |
| `simulated`     | Thông báo **giả lập** nhóm tự soạn để demo các tình huống thật quan sát trong `discord-pack` (bản cập nhật, hai thông báo mâu thuẫn). Hiển thị nhãn "giả lập (demo)" | `data/registry.json`        |
| `ingested`      | Thông báo nạp lúc chạy, **TA đã duyệt** (`SRC-xx`)                                                                                                                   | `data/runtime/entries.json` |
| `ta`            | Câu trả lời TA cho một cụm hàng chờ (`TA-xx`)                                                                                                                        | `data/runtime/entries.json` |

Khi triển khai thật: trỏ `ANNOUNCE_CHANNEL_ID` vào kênh thông báo của khoá → mọi thông báo mới tự thành đề xuất nguồn.
Nhóm không có quyền đưa bot vào server khoá, nên demo trên server test.

Sơ đồ kiến trúc, luồng và quyết định thiết kế: [ARCHITECTURE.md](ARCHITECTURE.md).

## Cấu trúc

| Đường dẫn                                     | Nội dung                                                                                                                       | Thật / mock                |
|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|----------------------------|
| `nopdung/decide.py`                           | **Quyết định trung tâm** (học viên): LLM → `FOUND / CONFLICT / CLARIFY / NOT_FOUND / OUT_OF_SCOPE`, guard bằng sổ nguồn, trace | **LLM thật**               |
| `nopdung/ingest.py`                           | **Nạp nguồn** (TA, augment): LLM trích xuất thông báo + phân loại quan hệ, guard, đề xuất chờ duyệt                            | **LLM thật**               |
| `nopdung/llm.py`                              | Gọi Gemini / OpenAI / Anthropic qua HTTP; thử lại khi 429 theo phút/5xx, dừng khi hết quota ngày                               | Thật                       |
| `nopdung/registry.py`                         | Sổ nguồn: phiên bản, thay thế toàn bộ / ghi đè theo lab, mâu thuẫn, hạn sắp tới                                                | Code                       |
| `nopdung/gaps.py`                             | Hàng chờ TA gom cụm + log phản hồi                                                                                             | Code                       |
| `nopdung/reminders.py`                        | Nhắc hạn tự đăng ký                                                                                                            | Code                       |
| `nopdung/digest.py`                           | Bản tin số liệu cho TA (không dùng LLM)                                                                                        | Code                       |
| `nopdung/render.py`                           | Thẻ trả lời dùng chung Discord/web                                                                                             | Code                       |
| `nopdung/storage.py`                          | Đọc/ghi JSON có khoá file + ghi nguyên tử (bot và web chạy cùng lúc)                                                           | Code                       |
| `nopdung/prompts/*.md`                        | System prompt của quyết định trung tâm và nạp nguồn                                                                            | Prompt                     |
| `tests/`                                      | 56 test pytest với LLM giả (không tốn quota)                                                                                   | Test                       |
| `bot/discord_bot.py`                          | Bot Discord (server test)                                                                                                      | Thật                       |
| `web/app.py`, `web/index.html`                | Web dự phòng khi pitch: tab Học viên, tab TA (hàng chờ, nạp thông báo, bản tin)                                                | Thật                       |
| `data/registry.json`                          | Sổ nguồn gốc                                                                                                                   | Fixture (public + giả lập) |
| `logs/decisions.jsonl`, `logs/ingest.jsonl`   | Trace mọi lời gọi LLM: system prompt, user prompt, raw response, guard, kết quả                                                | Log thật                   |
| `mock/`, `data/announcements.json`, `flow.md` | Bản mock CP2 (luật từ khoá)                                                                                                    | Mock CP2, giữ để đối chiếu |

## Lệnh Discord

| Ai       | Lệnh                                                                                                             | Việc                                        |
|----------|------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| Học viên | `/ask question:` hoặc tag `@DCC`                                                                                 | Hỏi nơi/cách/hạn nộp                        |
| Học viên | `/deadlines [hours]`                                                                                             | Hạn trong 48 giờ tới, mỗi dòng có mã nguồn  |
| Học viên | `/remind item [minutes_before]` · `/remind-off`                                                                  | Bật/tắt nhắc hạn qua DM                     |
| Học viên | `/sources`                                                                                                       | Các nguồn đang hiệu lực                     |
| TA       | `/source-add text [url]` · chuột phải tin → Apps → **Add to DCC sources** · đăng tin trong `ANNOUNCE_CHANNEL_ID` | Nạp thông báo → đề xuất nguồn trong kênh TA |
| TA       | `/ta-queue`                                                                                                      | Cụm câu hỏi chưa có nguồn / mâu thuẫn       |
| TA       | `/ta-digest [hours]`                                                                                             | Bản tin số liệu                             |

## Kiểm thử & lint

```bash
cd codebase
uv pip install -p .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m pytest -q tests          # 56 test, LLM giả
.venv/bin/ruff check . ../eval --config ruff.toml
```

CI GitHub Actions (`.github/workflows/ci.yml`) chạy ruff + pytest mỗi lần push/PR, không cần API key.

## Cài đặt (Python 3.11)

```bash
cd codebase
uv venv --python 3.11 .venv            # hoặc: python3.11 -m venv .venv
uv pip install -p .venv/bin/python -r requirements.txt
cp .env.example .env                   # điền API key + Discord token
```

## Chạy web demo

```bash
cd codebase
.venv/bin/uvicorn web.app:app --port 8000
```

Mở http://localhost:8000 — tab **Học viên** để hỏi, tab **Hàng chờ TA** để duyệt/nạp nguồn (sửa trực tiếp trước khi
duyệt). Thao tác TA chỉ chạy từ máy chạy server, hoặc đặt `WEB_TA_TOKEN` rồi nhập token khi trình duyệt hỏi.

## Chạy bot Discord (server test)

1. https://discord.com/developers/applications → **New Application** → tab **Bot** → **Reset Token**, dán vào
   `DISCORD_TOKEN`.
2. Tab **Bot** → bật **Message Content Intent** (để hỏi bằng cách tag bot).
3. Tab **OAuth2 → URL Generator**: scope `bot` + `applications.commands`; quyền `Send Messages`, `Embed Links`,
   `Read Message History`, `Use Slash Commands` → mở link, mời bot vào **server test**.
4. Discord bật Developer Mode → chuột phải server → Copy Server ID → `DISCORD_GUILD_ID`; tạo kênh `#ta-queue` (riêng tư
   cho TA) → `TA_CHANNEL_ID`; tạo kênh `#announcements` → `ANNOUNCE_CHANNEL_ID`; tạo role `TA` và gán cho người đóng vai
   TA.
5. Chạy:

```bash
cd codebase
.venv/bin/python -m bot.discord_bot
```

Kịch bản demo đầy đủ (khoảng 3 phút):

1. `/ask question: daily standup hạn khi nào?` → FOUND, nguồn TB-02, cảnh báo thay thế TB-01.
2. Trong `#announcements` đăng: `[CẬP NHẬT] Từ 18/09 khung nộp daily standup đổi thành 07:00–22:00.` → `#ta-queue` hiện
   đề xuất **UPDATE TB-02** → TA bấm **Duyệt** → hỏi lại câu 1 → nguồn `SRC-01`, hạn 07:00–22:00, cảnh báo thay thế
   TB-02.
3. `/ask question: Lab 3 lớp 3A hạn nộp khi nào?` → CONFLICT, cụm mới trong `#ta-queue`.
4. `/ask question: Lab 7 nộp ở đâu?` → NOT_FOUND → TA **Duyệt thành nguồn** → hỏi lại → FOUND `TA-01`.
5. `/deadlines` · `/remind item: Checkpoint Mini Hackathon` · `/ta-digest`.

Biệt danh bot trong server tự đặt theo `BOT_NICKNAME` (mặc định `DCC`). Muốn đổi **tên người dùng** của bot thì đổi
trong Developer Portal → Bot → Username.

## Hợp đồng đầu ra

```json
{
  "decision": "FOUND|CONFLICT|CLARIFY|NOT_FOUND|OUT_OF_SCOPE|ERROR",
  "item": "daily_standup|lab|de_tai|mentor_duty|hackathon_checkpoint|null",
  "lab": 3,
  "source_ids": [
    "TB-03",
    "TB-07"
  ],
  "missing": "item|lab|null",
  "topic": "...",
  "injection_detected": false,
  "note": null,
  "reason": "...",
  "superseded": [
    "TB-01"
  ],
  "trace_id": "...",
  "guards": [
    "..."
  ]
}
```

**Guard sau LLM** (ghi vào trace): bỏ mã nguồn không tồn tại · đổi bản `superseded` sang bản mới · nguồn bị TA ghi đè
riêng cho lab → dùng mục TA · hỏi bài lab mà thiếu số lab → CLARIFY · FOUND mà có mục active mâu thuẫn → CONFLICT ·
CONFLICT không thật → FOUND · lab không thuộc phạm vi nguồn → NOT_FOUND. Nơi/cách/hạn nộp hiển thị **lấy nguyên từ sổ
nguồn**, LLM không tự viết.

## Eval

```bash
codebase/.venv/bin/python eval/run_eval.py          # golden set quyết định trung tâm (27 case)
codebase/.venv/bin/python eval/run_ingest_eval.py   # bộ nạp nguồn (10 thông báo)
codebase/.venv/bin/python eval/run_eval.py H4c C05  # chạy vài case
python3 eval/kute_baseline.py                        # baseline bot Kute
```
