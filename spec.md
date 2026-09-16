# AI SPEC — Tra cứu yêu cầu nộp bài có dẫn nguồn · Nhóm DCC

**Lớp:** 3A · **Phòng:** E403 · **Cụm:** C3

**Đội trưởng:** Nguyễn Đức Danh — 2A202602722. Liên hệ: [TEAMMATES.md](TEAMMATES.md).

**Trạng thái:** Canvas CP1 (16/09/2026). Đã chốt Track B1, lát cắt, phân công và 2 người thử; evidence chuẩn B (mining)
và chuẩn A (khảo sát n=20) đã có; quality bar chốt tại CP4.

*Commit trước hạn chốt spec: 21:00 17/9, tại CP4 · quality bar chốt từ thời điểm nộp.*

> Cấu trúc phủ đúng "SPEC 8 phần" của chương trình: Bằng chứng (§1-§2) · Lát cắt (§4) · Canvas (đính kèm CP1) ·
> Augment/Automate (§4) · 4 đường đi của trải nghiệm (§6) · Kiểu lỗi (§5) · Kiểm thử (§7) · Phân công (§8). Hướng dẫn
> viết
> từng mục: `02-guide.md`.

**Track đã chọn:** B — Trợ lý Discord

**Hướng cụ thể / lát cắt trong Track B:** B1 — tra cứu yêu cầu nộp bài (daily standup / lab / đề tài) có dẫn nguồn chính
thức, tối ưu trợ lý Discord đang chạy. Form khảo sát chỉ hỏi trải nghiệm, không thu tên, mã học viên, lớp, email, số
điện
thoại hoặc thông tin liên hệ; người dùng thử được xác nhận riêng ngoài form.

Loại: [x] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job

### Canvas ô 1 — Thông tin chung, người dùng và công việc

- **Tên hướng đi:** Tra cứu yêu cầu nộp bài có dẫn nguồn (Track B1 — tối ưu trợ lý Discord).
- **Job executor:** Học viên AI20k K4 cần nộp một hạng mục bắt buộc (daily standup, bài lab, đề tài nhóm).
- **Core JTBD:** Khi chuẩn bị nộp một hạng mục bắt buộc, tôi cần xác định đúng nơi nộp, cách nộp và hạn nộp để được
  ghi nhận điểm danh/điểm.
- **Quy trình hiện tại (quan sát từ data pack):** Đọc thông báo/tin ghim → hỏi bot Trợ lý → hỏi lại bot hoặc hỏi Lab
  Coach/bạn học trên kênh → thử nộp (lệnh `/daily-standup`, VLearn, form) → bị chặn/muộn thì xin gia hạn.

### Canvas ô 2 — Nỗi đau và bằng chứng

**Problem statement:** Học viên K4 không xác định được nộp daily standup/lab/đề tài ở đâu, bằng cách nào và hạn đến khi
nào, phải hỏi lại nhiều lần trên Discord; một phần đã nộp muộn hoặc bị chặn nộp và mất điểm danh/XP.

**Evidence chuẩn B — mining `discord-pack` (12–14/09).** Phương pháp đếm, script tái lập và ví dụ đầy đủ:
[research/mining-evidence.md](research/mining-evidence.md).

| Chỉ số                                               | Giá trị                                                   |
|------------------------------------------------------|-----------------------------------------------------------|
| Câu hỏi về cách/nơi/hạn nộp / tổng câu hỏi của người | **28 / 275 (10,2%)** trong 3 ngày                         |
| Số tác giả khác nhau                                 | **18**                                                    |
| Hỏi trực tiếp bot Trợ lý                             | 21 / 28                                                   |
| Riêng daily standup                                  | 15 câu, 9 người; lặp lại liên tục sáng 14/09              |
| Đã nộp muộn / bị chặn / xin gia hạn                  | **8 câu** — hậu quả: mất điểm danh/XP, không nộp được lab |

Ví dụ nguyên văn (msg_id trong pack):

1. M57734 — "quy cách nộp daily standup, cả nhóm có phải nộp ko? … Nộp vào đâu?"
2. M65205 — "nộp ở đâu cơ, phần này mình đánh lệnh /daily-standup rồi mà ko được"
3. M82163 — "cái daly-standup sao m ghi là hết hôm nay nhưng nộp bài thì m kêu hết hạn."
4. M88027 — "Em lỡ nộp muộn 1 phút không submit bài được ạ"
5. M21463 — "em nhận được thông báo là em nộp muộn không được điểm danh"
6. M91752 — "mình có thể nộp đề tài nhóm mình chọn ở đâu"

**Evidence chuẩn A — khảo sát 20 học viên (16/09).** Log từng câu trả lời + quy tắc đếm:
[research/survey-results.md](research/survey-results.md).

| Chỉ số (n = 20)                                                    | Giá trị                                        |
|--------------------------------------------------------------------|------------------------------------------------|
| Gặp trở ngại khi tìm thông tin khoá học trên Discord               | **14/20 = 70%**                                |
| Lần gần nhất cần thông tin nộp bài/thủ tục **và** gặp trở ngại     | **10/20 = 50%** (9/19 nếu loại R19 nghi trùng) |
| Trở ngại phổ biến nhất: nhiều thông tin khác nhau / không tìm thấy | 6/20 và 3/20                                   |
| Mất ≥5 phút chủ động tìm/hỏi                                       | 11/20 = 55%                                    |
| Dùng bot nhưng phải hỏi lại/tìm nguồn khác                         | 8/15 người dùng bot = 53%                      |
| Trở ngại lặp lại ≥2 lần trong 7 ngày                               | 11/20 = 55%                                    |

Quote: R13 "Tài nguyên nằm ở đâu" → "Bị chậm deadline" · R02 "Cần biết link nộp bài" · R14 "Làm thông tin mình nhận
được chậm với không chuẩn".

**Đánh giá trung thực:** pain rộng đạt chuẩn A (70%). Pain đúng lát cắt chỉ 50% — chạm ngưỡng ≥50% của rubric nhưng
không đạt >50% của bài lab; chỉ 3/20 nêu đúng "hạn nộp/cách nộp". Lát cắt vì vậy dựa chính vào chuẩn B (mining), khảo
sát
bổ trợ. Form không thu định danh nên không xác minh được người trả lời ngoài nhóm/không trùng.

**Giới hạn:** pack chỉ 3 ngày onboarding, kênh public; 28 là cận dưới theo regex, không suy ra tỷ lệ toàn khóa.

## §2. Impact & quyết định chọn

### So sánh phương án

| Ứng viên                                           | Số người gặp / tần suất / chi phí mỗi lần                                                                             | Khả thi                                              | Quyết định                                         |
|----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|----------------------------------------------------|
| B1: Tra cứu yêu cầu nộp bài có nguồn               | Mining: 18 người / 28 câu trong 3 ngày, 8 câu muộn/bị chặn · Khảo sát: 10/20 vướng nộp bài/thủ tục, 11/20 mất ≥5 phút | Nguồn là thông báo chính thức, giới hạn được phạm vi | **Chọn** — bằng chứng nhiều nhất, hậu quả rõ       |
| B1: Hỏi lại thông tin thiếu và hướng dẫn chuyển TA | Chưa đếm riêng                                                                                                        | Cần xác định câu nào trả lời, câu nào chuyển người   | Loại làm lát cắt riêng; dùng làm nhánh trải nghiệm |
| B2: Tổng hợp câu hỏi còn tồn cho TA                | Chưa có bằng chứng từ phía TA                                                                                         | Cần thread/reply và quy trình TA hiện tại            | Loại — thiếu bằng chứng từ người dùng TA           |

Ứng viên "hỏi lại/chuyển TA" có tín hiệu từ khảo sát (8/15 người dùng bot phải hỏi lại) nhưng là hệ quả của cùng pain
nên gộp làm nhánh trải nghiệm.

### Canvas ô 3 — Lát cắt giải pháp

> **Học viên K4** cần **biết nộp một hạng mục bắt buộc (daily standup / lab / đề tài) ở đâu, như thế nào, hạn khi nào**
> được **AI chọn đoạn thông báo chính thức phù hợp và trả lời kèm trích dẫn (hoặc hỏi lại / chuyển TA khi không có căn
> cứ)** giúp **nộp đúng chỗ, đúng hạn mà không phải hỏi lại trên Discord**.

- **Một quyết định AI trung tâm:** Chọn nguồn chính thức phù hợp; trả lời kèm trích dẫn, hoặc hỏi lại/chuyển TA.
- **Đầu ra:** Nơi nộp, cách nộp, hạn nộp, trích dẫn nguồn; chỉ hiển thị thông tin có căn cứ.
- **Cách đo dự kiến:** Tỷ lệ trả đúng các trường so với nguồn; tỷ lệ từ chối/hỏi lại đúng khi không có căn cứ. Quality
  bar chốt tại CP4.

### Canvas ô 4 — Cam kết triển khai

- **Mức tự động hóa:** Conditional — trả lời khi có nguồn chính thức phù hợp; thiếu hạng mục/lớp thì hỏi lại; không có
  nguồn hoặc nguồn mâu thuẫn thì nói rõ giới hạn và hướng dẫn hỏi TA. Không tự gửi tin/tag TA.
- **Lý do (cost-of-error):** Sai nơi nộp hoặc deadline khiến học viên mất điểm danh/XP (M21463, M82163); không đoán
  thông
  tin quan trọng.
- **Phạm vi prototype:** Giao diện tra cứu web, lời gọi LLM thật ở quyết định trung tâm từ CP3. Kết nối Discord mô
  phỏng,
  ghi rõ trong `codebase/`.
- **Phân công:** Danh — spec, điều phối, nộp CP, slide; Chính — lõi AI (nguồn, prompt, API, trace); Cường — giao diện 4
  nhánh, HAX/PAIR, video demo; Duy — evidence, golden set, eval, validation log. Chi tiết tại §8.
- **Người thử 1:** Đinh Công Tú — học viên AI20k K4, ngoài nhóm (đã đồng ý).
- **Người thử 2:** Đỗ Phúc Hưng — học viên AI20k K4, ngoài nhóm (đã đồng ý).

## §3. Giải pháp tương tự đã nghiên cứu

- [Sản phẩm 1]: flow / đáng học / đáng né / mình khác gì
-

[Sản phẩm 2]: ...

## §4. Thiết kế

- Lát cắt MỘT CÂU: xem Canvas ô 3 ở §2.
- Non-goals (≥3 thứ KHÔNG build): không tra điểm/điểm danh/XP cá nhân; không tự nộp bài hay gia hạn thay học viên; không
  giải đáp kiến thức bài học; không tự tag/gửi tin cho TA.
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [ ] Working — phần nào mock, phần nào thật:
- Automation: [ ] augment [x] conditional [ ] automate — lý do theo cost-of-error: xem Canvas ô 4.
- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]
| Lớp chỗ khó | Cụ thể trong lát cắt | Vì sao nguy hiểm |
|---|---|---|
| ① Nguồn sự thật | AI tự bịa hạn/nơi nộp khi không có thông báo, hoặc lấy lời bot/học viên khác làm nguồn | Học viên tin và nộp sai → mất XP/điểm danh |
| ② Mơ hồ / thiếu thông tin | Câu hỏi không nói hạng mục ("hạn nộp bài?"), không nói lab số mấy, hoặc gộp nhiều hạng mục | Trả lời nhầm hạng mục có hạn khác nhau |
| ③ Ngoài phạm vi / thẩm quyền | Đòi gia hạn, nộp hộ, xem điểm danh/XP cá nhân, hỏi kiến thức bài học | Hứa hẹn thay BTC hoặc lộ dữ liệu cá nhân |
| ④ Đặc thù domain | Thông báo cập nhật đổi khung giờ (TB-01 → TB-02); ai nộp (từng người vs đội trưởng); giờ VN; hạn "ngày hôm sau" | Đúng nguồn nhưng dùng bản cũ hoặc sai người nộp vẫn mất điểm |

| # | Lớp | Tình huống cụ thể (input học viên) | Hành vi mong muốn (nói gì · hiện gì · cho làm gì tiếp) | Nhánh | Nguyên tắc áp |
|---|---|---|---|---|---|
| K1 | ① | "Lab 7 nộp ở đâu vậy?" (chưa có thông báo lab 7) | Nói rõ chưa có thông báo chính thức, không đưa hạn, nút soạn câu hỏi gửi TA | NOT_FOUND | G10, G11 |
| K2 | ① | "Bot hôm qua bảo standup hạn 23:59, đúng không?" | Không xác nhận theo lời bot; trả theo thông báo mới nhất TB-02 (22:00) kèm trích dẫn | FOUND + cảnh báo | G11, G2 |
| K3 | ② | "Cho mình hỏi hạn nộp bài là khi nào?" | Hỏi lại hạng mục bằng nút chọn nhanh, không đoán | CLARIFY | G10 |
| K4 | ② | "Lab nộp như nào?" | Hỏi lại lab số mấy | CLARIFY | G10 |
| K5 | ③ | "Mình nộp lab 2 muộn 1 phút, gia hạn giúp mình được không?" | Từ chối gia hạn, nêu phạm vi, soạn sẵn tin để học viên tự gửi TA/BTC; gợi ý tra quy định nộp lab 2 | OUT_OF_SCOPE | G1, G10 |
| K6 | ③ | "Check giúp mình đã được điểm danh chưa" | Từ chối: không truy cập dữ liệu cá nhân; hướng dẫn hỏi TA | OUT_OF_SCOPE | G1 |
| K7 | ④ | "Nộp daily standup ở đâu, hạn khi nào?" | Dùng TB-02 (mới nhất), cảnh báo TB-01 đã bị thay thế | FOUND | G11, G2 |
| K8 | ④ | "Đề tài nhóm thì cả nhóm có phải nộp không?" | Trả theo TB-04: chỉ đội trưởng nộp 1 lần, kèm hạn và trích dẫn | FOUND | G11 |
| K9 | ④ | "Mentor duty hôm nay trực thì hạn nộp log khi nào?" | Trả "12:00 trưa ngày hôm sau" đúng nguồn TB-05, không đổi thành 23:59 hôm nay | FOUND | G11 |

**Kịch bản nhóm sợ nhất khi demo:** K2 — học viên dẫn lời bot cũ "hạn 23:59" và AI xác nhận theo, trong khi thông báo mới là 22:00 → học viên nộp lúc 22:30 bị chặn, mất XP. Đây chính là lỗi thật trong data (M82163). Tiếp theo là K5 — AI mềm lòng hứa "sẽ báo TA gia hạn".

Các kịch bản K1–K9 sẽ vào golden set (`eval/`) ở CP3; mỗi lớp ≥2 case.

## §6. Bốn đường đi của trải nghiệm

ơ đồ luồng: [codebase/flow.md](codebase/flow.md). Tất cả nhánh bấm thử được trong `codebase/mock/index.html` (nút "Kịch bản demo").

| Đường đi | Khi nào | Học viên thấy gì | Làm gì tiếp |
|---|---|---|---|
| **Happy (FOUND)** | Có thông báo chính thức khớp hạng mục | Thẻ 3 trường Nơi nộp · Cách nộp · Hạn nộp + Lưu ý hậu quả + trích dẫn nguyên văn (mã TB, kênh, thời điểm) | Đi nộp; 👍/👎 hoặc sửa |
| **Low-confidence (CLARIFY, ②)** | Thiếu hạng mục hoặc số lab | 1 câu hỏi lại + nút chọn nhanh (Daily standup / Bài lab / Đề tài / Mentor duty; Lab 1…7) | Bấm 1 nút → bot trả lời lại |
| **Failure / không căn cứ (NOT_FOUND, ①)** | Không có thông báo chính thức khớp | "Chưa tìm thấy thông báo chính thức… không đưa ra hạn để tránh nộp sai" | Nút "Soạn câu hỏi gửi TA" (học viên tự copy gửi) hoặc hỏi hạng mục khác |
| **Correction (user sửa)** | Học viên thấy câu trả lời sai hạng mục/sai ý | Nút "✏️ Không phải cái tôi hỏi" → chọn lại hạng mục; 👎 → chọn "sai chỗ nào" | Bot trả lời lại theo lựa chọn mới; phản hồi được ghi nhận |

- **Khi bị đòi ngoài phạm vi (③):** nhãn OUT_OF_SCOPE, nêu rõ trợ lý chỉ tra nơi/cách/hạn nộp; không gia hạn, không nộp hộ, không
  xem điểm cá nhân; nút soạn tin gửi TA/BTC và nút "Tra quy định nộp thay vào đó".
- **Case đặc thù domain (④):** khi nhiều thông báo cùng hạng mục, luôn dùng bản `published` mới nhất và hiện cảnh báo vàng nêu
  mã thông báo bị thay thế; hiển thị rõ ai phải nộp (từng thành viên vs đội trưởng) lấy từ nguồn.

## §7. Kiểm thử

- Chiều chất lượng + định nghĩa kiểm chứng được:
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
- Quality bar (chốt từ hạn chốt spec của khoá, giữ nguyên sau đó): "Đạt khi ≥ ___% qua bộ, và ___"
- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

## §8. Phân công & kế hoạch

| Thành viên         | Mã học viên | Vai trò chính        | Phần việc cụ thể                                                                                                                                                                                 | Mốc chính     |
|--------------------|-------------|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| Nguyễn Đức Danh    | 2A202602722 | Đội trưởng · Product | spec §1–§4, §8–§9; bảng impact; nộp form CP1–CP5 bằng mã 2A202602722; slide 6 trang `demo-slides.pdf`; điều phối pitch                                                                           | CP1, CP4, CP5 |
| Bùi Gia Chính      | 2A202602693 | AI Engineer          | Kho nguồn chính thức (fixture soạn từ thông báo nộp bài); prompt chọn nguồn + trả lời có trích dẫn/hỏi lại/từ chối; lời gọi LLM thật; trace log prompt + raw response trong `codebase/`; spec §5 | CP3           |
| Lê Phan Việt Cường | 2A202602641 | Frontend/UX          | Mock CP2 trong `codebase/` với 4 nhánh (happy / low-confidence / không căn cứ / correction); nối UI với module AI; bảng HAX/PAIR §4b và §6; video 30s CP3 + video demo dự phòng                  | CP2, CP3, CP5 |
| Nguyễn Quang Duy   | 2A202602426 | Research & Eval      | Tổng hợp khảo sát + mining trong `research/`; `eval/golden_set.json` ≥20 case (≥10 từ msg_id thật, ≥2 case/lớp chỗ khó); script chạy eval; `eval/run_results.md`; spec §7; `validation/`         | CP3, CP4, CP5 |

Cả 4 người tự viết `reflection/<MSHV>_<Ten>.md` và phải giải thích được phần có tên mình khi pitch.

- Willing users: **Đinh Công Tú**, **Đỗ Phúc Hưng** (học viên AI20k K4, ngoài nhóm) — đã đồng ý thử. Kế hoạch validation:
  sáng 18/9 thử prototype với 2 người này và ≥3 người ngoài nhóm khác; giao task "tìm cách/nơi/hạn nộp daily standup
  hoặc lab", quan sát im lặng, ghi điểm vướng và quote nguyên văn vào `validation/user_testing_log.md`.
- Multi-prototype: không làm.

## §9. Changelog

| Thời điểm  | Đổi gì                                                                                                        | Vì sao (trỏ về feedback/case nào)                                                          |
|------------|---------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| 16/09/2026 | Cập nhật nhóm 4 thành viên, Nguyễn Đức Danh là đội trưởng, chọn Track B; đồng bộ README.md và TEAMMATES.md    | Theo xác nhận của nhóm; chưa phải thay đổi từ validation người dùng                        |
| 16/09/2026 | Soạn Canvas nháp 4 ô ở §1–§2 cho ứng viên B1; thêm phân công đề xuất và các trường bằng chứng cần bổ sung     | Theo yêu cầu soạn bản nháp trước khảo sát; không khai kết quả hoặc người thử chưa xác nhận |
| 16/09/2026 | Chốt B1; mở rộng lát cắt từ "bài lab" sang "hạng mục bắt buộc"; thêm evidence chuẩn B, phân công, 2 người thử | Mining: 15/28 câu hỏi về nộp là daily standup, không chỉ lab (research/mining-evidence.md) |
| 16/09/2026 | Thêm evidence chuẩn A (khảo sát n=20) và đánh giá trung thực mức xác nhận theo lát cắt                        | research/survey-results.md                                                                 |
