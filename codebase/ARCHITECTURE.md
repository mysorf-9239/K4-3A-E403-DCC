# Kiến trúc — Bot DCC

## Tổng quan hệ thống

```mermaid
flowchart LR
    subgraph Users[Người dùng]
        HV[Học viên]
        TA[TA / Lab Coach]
    end
    subgraph Channels[Kênh]
        DC[Bot Discord<br/>bot/discord_bot.py]
        WEB[Web dự phòng<br/>web/app.py + index.html]
    end
    subgraph Core[Lõi dcc]
        DEC[decide.py<br/>Quyết định trung tâm]
        ING[ingest.py<br/>Nạp nguồn]
        REG[(registry.py<br/>Sổ nguồn có phiên bản)]
        GAP[gaps.py<br/>Hàng chờ TA]
        REM[reminders.py<br/>Nhắc hạn opt-in]
        DIG[digest.py<br/>Bản tin số liệu]
        RND[render.py<br/>Thẻ trả lời]
        LLM[llm.py<br/>Rate limit + retry]
    end
    subgraph Data[Dữ liệu]
        SEED[data/registry.json<br/>public_doc + simulated]
        RT[data/runtime/*.json<br/>mục TA/nạp, hàng chờ, nhắc hạn]
        LOG[logs/*.jsonl<br/>trace prompt + raw response]
    end
    GEM[Gemini / OpenAI / Anthropic]
    HV -->|/ask, @DCC, /deadlines, /remind| DC
    HV --> WEB
    TA -->|/source - add, chuột phải, #announcements,<br/>duyệt, /ta - digest| DC
    TA --> WEB
    DC --> DEC & ING & GAP & REM & DIG
    WEB --> DEC & ING & GAP & DIG
    DEC --> RND
    DEC & ING --> LLM --> GEM
    DEC & ING & REM & DIG --> REG
    REG --- SEED & RT
    DEC & ING --> LOG
    GAP --- RT
```

## Luồng học viên hỏi (quyết định AI trung tâm)

```mermaid
sequenceDiagram
    participant HV as Học viên
    participant B as Bot DCC
    participant D as decide.py
    participant L as LLM
    participant R as Sổ nguồn
    HV ->> B: /ask "Lab 3 lớp 3A hạn khi nào?"
    B ->> D: decide(question)
    D ->> D: cache? (câu hỏi + sổ nguồn chưa đổi)
    D ->> R: load_entries()
    D ->> L: system prompt + sổ nguồn + <cau_hoi>
    L -->> D: JSON {decision, item, lab, source_ids}
    D ->> R: guard: nguồn có thật? đúng hạng mục? đúng lớp? bản mới nhất? ghi đè? mâu thuẫn?
    D -->> B: CONFLICT [TB-07, TB-03] + trace_id
    B ->> B: gaps.add() →#ta-queue
    B -->> HV: Embed: 2 nguồn, cảnh báo, nút sửa/👍👎
```

## Luồng nạp nguồn (AI đề xuất, TA quyết định)

```mermaid
flowchart TD
  A[Thông báo mới<br/>#announcements / chuột phải / source-add] --> B[ingest.propose: LLM trích xuất]
  B --> C{Guard bằng code}
  C -->|hạng mục lạ| X[Bỏ]
  C --> D[Quan hệ: NEW / UPDATE / CONFLICT / DUPLICATE]
  D --> E[Đề xuất trong #ta-queue]
  E -->|Duyệt / Sửa rồi duyệt / Thay thế / Song song| F[registry.add_entry]
  E -->|Bỏ qua| Y[rejected]
  F --> G{Phạm vi}
  G -->|toàn bộ| H[Mục cũ superseded]
  G -->|một lab / một mốc CPx| I[Ghi đè cục bộ, phần còn lại giữ nguyên]
```

## Quyết định thiết kế

| Quyết định      | Lựa chọn                                                                                            | Lý do                                                                                                                                                    |
|-----------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Truy xuất nguồn | Đưa toàn bộ sổ nguồn (~10–20 mục) vào prompt, **không dùng RAG/vector DB**                          | Sổ nhỏ; đưa đủ ngữ cảnh giúp LLM thấy quan hệ thay thế/mâu thuẫn giữa các mục — RAG top-k có thể bỏ sót mục mâu thuẫn. Chuyển sang RAG khi sổ > ~200 mục |
| Tin LLM đến đâu | LLM chọn quyết định + mã nguồn; **code guard kiểm tra lại**; nội dung hiển thị lấy nguyên văn từ sổ | Hai lượt eval liền LLM bỏ sót mâu thuẫn Lab 3 → guard là bắt buộc; không để LLM viết hạn nộp                                                             |
| Mức tự động hoá | Học viên: conditional · Nạp nguồn: augment (TA duyệt) · Nhắc hạn: opt-in                            | Sai hạn/nơi nộp làm mất điểm; ghi sai sổ ảnh hưởng mọi người                                                                                             |
| Framework agent | Python thuần, không LangGraph                                                                       | Luồng tuyến tính một bước quyết định; ít phụ thuộc, dễ giải thích và test                                                                                |
| Lưu trữ         | File JSON + khoá `fcntl` + ghi nguyên tử                                                            | Đủ cho demo một máy; production chuyển SQLite/PostgreSQL                                                                                                 |
| Chống quota     | Rate limit phía client, retry theo gợi ý provider, cache 10 phút theo dấu vân tay sổ nguồn          | Gemini free tier 15 request/phút                                                                                                                         |
| Giờ             | `APP_TIMEZONE=Asia/Ho_Chi_Minh`                                                                     | Hạn nộp không lệch khi chạy trên máy/server khác múi giờ                                                                                                 |
| Bảo mật web     | Thao tác TA cần `X-TA-Token` hoặc chỉ từ localhost                                                  | Không mở nút duyệt nguồn ra mạng                                                                                                                         |

## Giới hạn đã biết

- Không tích hợp vào server khoá hay bot Kute thật (không có quyền) — demo ở server test; VLearn chỉ nằm trong kế hoạch.
- Sổ nguồn gốc: 1 mục tài liệu công khai thật (lịch CP), 6 mục giả lập có gắn nhãn.
- Mục nguồn mô tả được hạng mục, lab, lớp và mốc hiệu lực, nhưng **chưa mô tả được phạm vi áp dụng theo buổi học**
  (daily standup áp dụng cho buổi build, LAB hay LEC). Vì thiếu trường này, guard không kiểm được câu hỏi kiểu đó và
  LLM tự suy — case HO07 trong `eval/heldout_results.md` vẫn trượt vì lý do này.
- Bot và web cùng ghi file có khoá, nhưng lưu trữ file không phù hợp nhiều instance.
- Free tier Gemini: dưới tải lớn request sẽ phải chờ (rate limit) thay vì lỗi.
