# Reflection — Lê Phan Việt Cường

Frontend/UX nhóm DCC · 2A202602641 · lớp 3A, phòng E403, cụm C3

## Vai trò và phần việc của tôi

Tôi làm phần học viên và TA thật sự nhìn thấy: con bot trên Discord, trong
[`codebase/bot/discord_bot.py`](../codebase/bot/discord_bot.py).

Tám lệnh: `/ask`, `/deadlines`, `/sources`, `/remind`, `/remind-off`, `/ta-queue`, `/ta-digest`, `/source-add`. Năm kiểu
embed cho năm loại quyết định, mỗi kiểu một màu và một dòng **📌 Nguồn** không bao giờ được thiếu — kể cả khi bot không
trả lời được thì cũng phải nói rõ là nó không tìm thấy nguồn nào, chứ không nói vòng vo. Ngoài ra là menu chọn hạng mục
và chọn số lab khi câu hỏi thiếu thông tin, nút 👍/👎 kèm menu lý do, nút "✏️ Không phải cái tôi hỏi", và hai modal cho
TA: "Duyệt thành nguồn" cho cụm câu hỏi trong hàng chờ, và "Sửa rồi duyệt" cho đề xuất nguồn mà AI trích chưa chuẩn.

Một chi tiết tôi khá ưng: mọi nút đều có `custom_id` cố định (`dcc:approve:<id>`, `dcc:proposal:<action>:<id>`) và bot
gắn lại view lúc khởi động. Nghĩa là TA mở Discord hôm sau, bấm vào nút cũ trong lịch sử kênh, nó vẫn chạy. Lần đầu tôi
làm thì không như vậy — restart bot một cái là mọi nút thành đồ trang trí.

Tôi cũng làm bản web dự phòng [`codebase/web/`](../codebase/web/) dùng chung đúng lõi `dcc/` (phòng khi hôm demo Discord
hoặc mạng có vấn đề), quay video CP3 30 giây, và cùng Danh dựng video demo dự phòng 4 phút 33 giây cho CP5.

## AI đã hỗ trợ thế nào

discord.py là thư viện tôi chưa dùng bao giờ. AI giúp tôi đi nhanh qua phần khung — đăng ký slash command, dựng View và
Modal, chỗ nào cần `defer()` vì gọi LLM lâu hơn 3 giây — và chỗ này đúng là tiết kiệm cho tôi vài tiếng đọc tài liệu.

Nhưng phần bố cục embed thì tôi tự sửa gần hết. Bản AI viết ra nhồi rất nhiều field, đọc trên điện thoại là thành một
khối chữ. Tôi cắt xuống còn ba thứ theo đúng thứ tự người ta cần: **trả lời** → **nguồn** → **cảnh báo nếu có** (mốc này
đã bị thay thế, hoặc mới cập nhật một phần). Cách sắp xếp này tôi giữ nguyên cho cả năm loại quyết định để người dùng
không phải học lại chỗ nhìn.

Điều tôi rút ra khi làm với AI phần giao diện: nó viết code chạy được rất nhanh, nhưng nó không biết người dùng đang
đứng ở đâu khi đọc cái embed đó. Chỗ đó vẫn phải là mình.

## Một lỗi của nhóm và điều tôi rút ra

Lỗi tôi chọn là lỗi **của chính phần tôi làm**, và nó chỉ lộ ra khi nhóm quay video demo dự phòng sáng 18/09.

Kịch bản là: học viên hỏi trống "hạn nộp là khi nào?", bot trả CLARIFY và đưa menu năm hạng mục, học viên bấm chọn
"Mentor duty". Đúng ra bot phải trả lời ngay. Nhưng nó hỏi lại — hiện đúng cái menu vừa bấm thêm lần nữa.

Lý do là luồng của tôi có gửi lựa chọn đó xuống `decide` dưới dạng `hint`, nhưng model vẫn trả CLARIFY, và không có gì
chặn lại. Trong test thì luồng này pass vì tôi test "bấm menu có gọi lại `decide` không", chứ không test "bấm menu xong
người dùng có nhận được câu trả lời không". Hai câu hỏi đó không giống nhau, và tôi test nhầm câu dễ hơn.

Nhóm sửa bằng một guard mới: nếu học viên đã bấm chọn hạng mục thì không được hỏi lại hạng mục nữa
(`hint_answers_clarify->FOUND`), trừ trường hợp còn thiếu số lab thì hỏi tiếp là hợp lý. Kèm 2 test mới.

Bài học thật sự của tôi không nằm ở đoạn code đó, mà ở chỗ: **lỗi này sống trong repo suốt và không bộ test nào bắt
được, vì golden set đo câu trả lời cho một câu hỏi đơn, còn đây là lỗi của một chuỗi hai bước.** Nếu hôm ấy nhóm không
quay video thì rất có thể giám khảo mới là người bấm ra nó. Từ giờ tôi sẽ coi việc tự đi hết một lượt bằng tay như một
bước bắt buộc, ngang với chạy test.

## Nếu làm lại tôi sẽ làm khác ở đâu

1. **Viết test theo chuỗi thao tác, không chỉ theo hàm.** Ít nhất một test cho mỗi đường đi nhiều bước: hỏi mơ hồ → chọn
   menu → nhận trả lời; trả lời sai → bấm "Không phải cái tôi hỏi" → nhận trả lời mới.
2. **Đi hết kịch bản bằng tay sau mỗi lần đổi luồng**, thay vì để dồn đến lúc quay video mới đi. Buổi quay hôm đó lộ ra
   đúng một lỗi, và tôi nghĩ nếu đi sớm hơn thì còn lộ ra nữa.
3. **Cho người ngoài nhóm bấm thử sớm.** Suốt hai ngày chỉ có bốn đứa tôi bấm con bot này, mà bốn đứa thì đã biết trước
   nó hoạt động ra sao. Nhóm khai 2 willing user từ CP1 và cuối cùng không mời được ai — phần giao diện là phần thiệt
   nhất vì chuyện đó.
