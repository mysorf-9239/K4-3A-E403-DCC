# Reflection — Nguyễn Quang Duy

Research & Eval nhóm DCC · 2A202602426 · lớp 3A, phòng E403, cụm C3

## Vai trò và phần việc của tôi

Tôi lo phần đo: nhóm nói con bot tốt hơn cái đang có thì tôi phải đưa ra được con số, và con số đó phải chạy lại được.

Tôi xây [`eval/golden_set.json`](../eval/golden_set.json) — 27 case, trong đó 15 câu lấy thẳng từ tin nhắn thật trong
`discord-pack` (tôi giữ `msg_id` cho từng câu để ai cũng tra ngược được), còn lại là case tôi dựng để phủ đủ bốn lớp chỗ
khó. Mỗi case tôi không chỉ ghi "đáp án đúng" mà ghi luật chấm: quyết định nào được chấp nhận, nguồn nào **bắt buộc**
phải có, nguồn nào **cấm** dùng. Nhờ vậy [`run_eval.py`](../eval/run_eval.py) chấm tự động từ trace được, không ai phải
ngồi chấm tay và không ai chấm lệch nhau.

Với 15 câu thật, tôi còn chép lại **câu trả lời thật của bot Kute** cho đúng tin nhắn đó vào trường `kute_baseline`
(có trả lời không, có dẫn nguồn không, có hỏi lại thừa không, có chuyển Mod không). Đó là baseline để so, và nó cho ra
con số mà nhóm dùng ở slide: Kute trả lời 0/15 câu có nguồn kiểm chứng được, lặp lại FAQ "0h–10h" 11 lần.

Ngoài ra tôi làm bộ nạp nguồn 10 thông báo với [`run_ingest_eval.py`](../eval/run_ingest_eval.py), chạy và ghi 3 lượt
golden đầu, viết bộ test pytest dùng LLM giả (hiện 56 test) và giữ CI xanh, và chuẩn bị kịch bản buổi thử trong
[`validation/user_testing_log.md`](../validation/user_testing_log.md).

## AI đã hỗ trợ thế nào

Tôi dùng AI nhiều nhất ở hai chỗ, và cả hai chỗ đều phải kiểm lại bằng tay.

Chỗ thứ nhất là **sinh case**. Tôi đưa tin nhắn thật rồi nhờ viết thêm biến thể. Vấn đề là biến thể AI sinh ra rất giống
nhau — cùng một câu hỏi viết lại bằng từ khác, chứ không phải một tình huống khác. Tôi bỏ khá nhiều và tự viết lại theo
bốn lớp chỗ khó, để mỗi case thật sự hỏng theo một kiểu riêng.

Chỗ thứ hai là **script chấm**. AI viết `run_eval.py` nhanh, nhưng bản đầu chấm hơi dễ dãi: chỉ so loại quyết định. Tôi
sửa để nó so cả danh sách nguồn, và thêm `forbid_sources`. Ngay sau đó số lượt đạt tụt xuống, và đó mới là số thật.

Tôi cũng dùng AI để viết 56 test với LLM giả. Phần này thì tin được, vì test không có gì để "đoán": đầu vào cố định,
đầu ra cố định.

## Một lỗi của nhóm và điều tôi rút ra

Lỗi tôi chọn là lỗi của chính bộ đo tôi xây: **golden set 27 case đạt 100% bốn lượt liên tiếp, nhưng bộ held-out 22 câu
chỉ đạt 19/22 = 86,4% và trượt quality bar.**

Lúc thấy 27/27 tôi có thật sự thấy yên tâm. Đến khi Danh viết bộ held-out và chạy, ba case trượt cho tôi thấy vấn đề
không nằm ở model mà nằm ở bộ đo của tôi:

- **HO14** (Lab 3 lớp **3B**) — trong 27 case của tôi, mọi câu hỏi về Lab 3 đều là lớp 3A. Tôi không có case nào đổi
  lớp, nên guard mâu thuẫn nhìn có vẻ đúng suốt bốn lượt, trong khi nó sai với mọi lớp khác.
- **HO07** (daily standup áp dụng cho buổi LAB/LEC hay chỉ build phase) — tôi không có case nào hỏi về *phạm vi áp dụng*
  của một quy định. Toàn bộ 27 case của tôi đều hỏi "ở đâu, cách nào, hạn khi nào".
- **HO22** (câu hỏi quy định nộp bài lẫn trong một tin toàn lỗi kỹ thuật) — tôi có E01 gần giống, nhưng ở E01 phần nộp
  bài viết rất rõ, nên case của tôi dễ hơn case thật.

Nói cách khác: bộ đo của tôi đạt 100% **vì nó thiếu chiều, chứ không phải vì hệ thống đúng**. Prompt và guard được sửa
đi sửa lại trên đúng 27 case đó suốt hai ngày, nên chúng dần dần vừa khít với bộ đo — chính là cái mà tài liệu gọi là
overfit bộ đo. Tôi từng đọc ý này nhưng chỉ đến khi nhìn con số của mình tụt từ 100% xuống 86,4% tôi mới thật sự hiểu.

Bài học: **một bộ đo chỉ nói được điều gì đó khi nó chưa từng được dùng để sửa hệ thống, và khi nó có case đổi từng
chiều của câu hỏi** — đổi lớp, đổi lab, đổi cách diễn đạt, đổi thứ người ta thật sự muốn biết. Tôi giữ nguyên bar và
ghi nguyên kết quả 19/22 vào [`eval/heldout_results.md`](../eval/heldout_results.md), kể cả khi nó làm bài của nhóm xấu
đi, vì số liệu sửa cho đẹp thì không còn dùng được vào việc gì.

## Nếu làm lại tôi sẽ làm khác ở đâu

1. **Chia đôi bộ case ngay từ đầu.** Gom 40 câu ở CP3, cất 13 câu vào file không ai được mở cho tới khi chốt bar. Chi
   phí gần như bằng 0, mà toàn bộ vấn đề ở trên đã tránh được.
2. **Dựng case theo lưới, không theo cảm tính.** Mỗi chiều một trục — hạng mục × lớp × lab có/không trong sổ × cách viết
   (chuẩn, teencode, tiếng Anh) × ý định lẫn lộn — rồi lấy mẫu trên lưới đó. Bộ held-out về sau làm đúng kiểu này và nó
   bắt lỗi ngay, còn bộ golden của tôi thì không.
3. **Tách lỗi hạ tầng khỏi lỗi mô hình ngay từ lượt đầu.** Lượt golden 1 có case E01 trượt chỉ vì lỗi 429 hết quota, mà
   lúc đó nhóm mất một lúc mới biết đó không phải lỗi quyết định. Về sau `run_eval.py` đếm riêng "lỗi gọi LLM" — nhẽ ra
   cột đó phải có từ lượt đầu tiên.
4. **Chốt lịch buổi thử người dùng thay vì chỉ chuẩn bị kịch bản.** Tôi viết xong kịch bản 10 phút, bốn task và bảng log
   trong `validation/`, nhưng nhóm không tổ chức được buổi nào trước hạn CP5. Chuẩn bị mà không có lịch và người cụ thể
   thì vẫn là con số 0.
