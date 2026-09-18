# Reflection — Lê Phan Việt Cường

Frontend/UX nhóm DCC · 2A202602641 · lớp 3A, phòng E403, cụm C3

## Vai trò và phần việc của tôi

Tôi phụ trách phần giao diện và trải nghiệm sử dụng của sản phẩm. Phần chính của tôi là bot Discord trong
[`codebase/bot/discord_bot.py`](../codebase/bot/discord_bot.py), tức là phần mà học viên và TA trực tiếp nhìn thấy và thao tác.

Bot có tám lệnh: `/ask`, `/deadlines`, `/sources`, `/remind`, `/remind-off`, `/ta-queue`, `/ta-digest` và
`/source-add`. Khi học viên đặt câu hỏi, bot trả lời bằng embed có nội dung, nguồn tham khảo và cảnh báo nếu cần. Nếu câu hỏi còn thiếu thông tin, bot hiện menu để người dùng chọn hạng mục hoặc số lab, thay vì tự đoán. Tôi cũng làm các nút 👍/👎, menu chọn lý do khi câu trả lời sai, nút "✏️ Không phải cái tôi hỏi", cùng hai modal cho TA: "Duyệt thành nguồn" và "Sửa rồi duyệt".

Một chi tiết kỹ thuật tôi thấy khá đáng giá là các nút TA cần dùng lâu dài, như nút duyệt câu hỏi trong hàng chờ và các nút xử lý đề xuất nguồn, đều có `custom_id` cố định. Khi bot khởi động lại, `setup_hook()` gắn lại các view của gap và proposal đang mở. Nhờ vậy, TA vẫn có thể bấm các nút trong tin nhắn cũ. Lúc đầu tôi chưa xử lý phần này nên cứ restart bot là các nút cũ không dùng được nữa.

Ngoài Discord, tôi làm thêm bản web dự phòng trong [`codebase/web/`](../codebase/web/). Bản web dùng chung lõi `dcc/` với bot, để nhóm vẫn có thể demo nếu Discord gặp sự cố. Tôi cũng quay video thao tác CP3 dài 30 giây và cùng Danh dựng video demo dự phòng dài 4 phút 33 giây cho CP5.

## AI đã hỗ trợ thế nào

Trước dự án này tôi chưa từng dùng `discord.py`, nên tôi dùng AI coding assistant để dựng phần khung ban đầu: đăng ký slash command, tạo `View` và `Modal`, và xử lý `defer()` cho những lượt gọi LLM có thể mất hơn ba giây. Phần hỗ trợ này giúp tôi tiết kiệm khá nhiều thời gian đọc tài liệu và có một phiên bản chạy được sớm để thử trên Discord.

Tuy nhiên, giao diện ban đầu do AI gợi ý chưa phù hợp để đọc trên điện thoại. Embed có quá nhiều field nên nhìn khá rối. Tôi tự rút gọn và sắp xếp lại theo thứ tự người dùng cần: **câu trả lời** → **nguồn** → **cảnh báo nếu có**. Tôi giữ cách trình bày này nhất quán cho các trạng thái FOUND, CLARIFY, CONFLICT, NOT_FOUND và OUT_OF_SCOPE để người dùng không phải tìm lại thông tin ở mỗi loại câu trả lời.

Điều tôi rút ra là AI có thể giúp viết nhanh một đoạn code chạy được, nhưng không tự biết người dùng đang nhìn giao diện trên thiết bị nào, cần đọc thông tin gì trước, hay đang bị vướng ở bước nào. Những quyết định đó vẫn cần người làm sản phẩm tự kiểm tra và điều chỉnh.

## Một lỗi của nhóm và điều tôi rút ra

Lỗi tôi chọn nằm ngay trong luồng giao diện do tôi phụ trách. Nhóm phát hiện lỗi này khi quay video demo dự phòng vào sáng 18/09.

Kịch bản xảy ra như sau: học viên hỏi một câu chưa rõ hạng mục, chẳng hạn "Hạn nộp là khi nào?". Bot trả về CLARIFY và hiện menu năm hạng mục. Sau khi học viên chọn "Mentor duty", đáng lẽ bot phải dùng lựa chọn đó để trả lời ngay. Nhưng bot lại hiện đúng menu vừa bấm và hỏi thêm một lần nữa.

Nguyên nhân là lựa chọn của người dùng đã được gửi xuống `decide` dưới dạng `hint`, nhưng model vẫn trả về CLARIFY và
hệ thống chưa có bước nào chặn việc hỏi lặp. Test cũ chỉ kiểm tra rằng sau khi bấm menu, bot có gọi lại `decide` hay
không. Nó chưa kiểm tra kết quả cuối cùng mà người dùng nhận được, nên vẫn pass dù luồng thực tế bị lặp.

Nhóm sửa lỗi bằng guard `hint_answers_clarify->FOUND` trong
[`codebase/dcc/decide.py`](../codebase/dcc/decide.py). Nếu người dùng đã chọn hạng mục thì hệ thống dùng luôn lựa chọn
đó, không hỏi lại. Riêng trường hợp chọn "Bài lab" nhưng chưa có số lab thì bot vẫn phải hỏi tiếp. Nhóm bổ sung hai test
cho hai trường hợp này trong [`codebase/tests/test_decide.py`](../codebase/tests/test_decide.py).

Bài học lớn nhất của tôi là test một hàm chạy đúng chưa chắc đã chứng minh trải nghiệm người dùng chạy đúng. Lỗi này nằm
trong một chuỗi hai bước: hỏi câu mơ hồ → chọn menu → nhận câu trả lời. Golden set chủ yếu kiểm tra từng câu hỏi độc lập
nên không phát hiện được. Nếu nhóm không tự đi hết luồng khi quay video, rất có thể giám khảo sẽ là người tìm ra lỗi đó
trong lúc demo.

## Nếu làm lại tôi sẽ làm khác ở đâu

1. Tôi sẽ viết test theo cả chuỗi thao tác, không chỉ test từng hàm riêng lẻ. Ví dụ: hỏi câu mơ hồ → chọn hạng mục →
   nhận câu trả lời; hoặc nhận câu trả lời sai → bấm "Không phải cái tôi hỏi" → chọn lại → nhận kết quả mới.
2. Sau mỗi lần sửa luồng giao diện, tôi sẽ tự đi lại toàn bộ kịch bản chính trên Discord. Việc này nên được làm thường
   xuyên, thay vì chờ đến lúc quay video mới kiểm tra từ đầu đến cuối.
3. Tôi sẽ mời người ngoài nhóm dùng thử sớm hơn. Bốn thành viên trong nhóm đều đã biết bot hoạt động như thế nào nên dễ
   bỏ qua những chỗ gây khó hiểu cho người dùng mới. Nhóm đã ghi tên willing user từ CP1 nhưng cuối cùng không tổ chức
   được buổi thử đúng kế hoạch, và phần giao diện là phần chịu ảnh hưởng rõ nhất.
