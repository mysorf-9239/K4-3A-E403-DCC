# Reflection - Nguyễn Đức Danh

Đội trưởng nhóm DCC - 2A202602722 - lớp 3A, phòng E403, cụm C3

## Vai trò và phần việc của tôi

Là đội trưởng, phần việc chính: `spec.md` cùng toàn bộ phần bằng chứng và phần đo ở giai đoạn sau và điều phối giữa các
thành viên.

Ngày 16/09, xem `data/discord-pack` để đếm số học viên K4 thật sự vướng ở đâu. Ghi lại cách đếm và câu lệnh chạy tại [
`research/mining-evidence.md`](../research/mining-evidence.md): 28 trên 275 câu hỏi trong pack là về nộp bài, 18 người
hỏi, và 7 tin cho thấy đã muộn hoặc bị chặn nộp - 5 trong số đó vì không rõ khung giờ. Song song làm form khảo sát,
thu được 20 người ngoài nhóm trả lời, 14 người xác nhận đã gặp trở ngại ([
`research/survey-results.md`](../research/survey-results.md), log nguyên văn ở `survey-raw.csv`).

Từ CP4 kiêm luôn phần đo. Tôi viết [`eval/quality_bar.py`](../eval/quality_bar.py) và chốt quality bar Q1–Q8 bằng con số
vào chiều 17/09, rồi viết bộ held-out 22 câu ([`eval/heldout_set.json`](../eval/heldout_set.json)) - 13 câu lấy từ tin
nhắn thật chưa dùng ở golden, 9 câu tôi tự dựng theo User Input Grid (lớp khác, lab chưa có trong sổ, teencode, tiếng
Anh, injection giả dạng thông báo, nhờ nộp hộ). Tôi chạy nó một lượt và ghi nguyên kết quả vào[
`eval/heldout_results.md`](../eval/heldout_results.md). Ngoài ra làm `codebase/ARCHITECTURE.md`, cấu hình ruff và
CI, phiếu chấm độc lập, slide và video demo dự phòng, và nộp form từ CP1 đến CP5.

## AI đã hỗ trợ thế nào

Tôi dùng Claude Code gần như suốt hai ngày, nhưng ở hai chế độ khác nhau.

Với phần đếm dữ liệu, tôi chỉ nhờ AI viết script lọc và gom nhóm, con số cuối cùng tôi tự mở file kiểm lại, vì đây là
thứ giám khảo có thể bắt tôi chạy lại tại chỗ. Việc kiểm này không thừa: bản spec đầu tôi viết "8 tin đã có hậu quả",
đến lúc soi lại từng `msg_id` thì chỉ có 7 tin là chuyện đã xảy ra, còn M35080 là một câu hỏi giả định. Tôi sửa xuống 7.

Với phần viết spec thì ngược lại - tôi để AI nêu chỗ hổng, còn nội dung tôi tự quyết. Lần rà trước CP4, AI chỉ ra hai
chỗ tôi đang tự cho điểm mình quá cao: nhóm khai mức prototype "Working" trong khi 6 trên 7 mục sổ nguồn là giả lập
(đúng định nghĩa thì là Mock), và golden set 100% không nói lên gì vì prompt với guard đều đã sửa trên chính 27 case đó.
Cả hai chỗ tôi đều sửa theo.

## Một lỗi của nhóm và điều tôi rút ra

Lỗi tệ nhất là **quality bar của nhóm được viết sau khi đã nhìn thấy kết quả 4 lượt golden**. Lúc đó nghĩ đơn giản là
"đo xong rồi thì biết đặt ngưỡng ở đâu cho hợp lý", nhưng đó chính là tự đặt vạch đích sau khi đã chạy tới nơi. Bar 85%
của tôi không phải cam kết, nó là mô tả.

Cách chữa cháy là viết bộ held-out 22 câu **cùng lúc** với bar và chạy sau đó, không sửa prompt hay guard ở giữa. Kết
quả làm tôi tỉnh ra: 19/22 = 86,4%, vượt ngưỡng tổng nhưng trượt bar vì hai nhóm case chỉ đạt 66,7% và có một câu trả
lời vượt quá thứ sổ nguồn nói (HO07) - mà Q2 là điều kiện cứng. Nhóm sửa được 2 trong 3 case trượt, lượt 2 lên 21/22,
HO07 vẫn trượt và giữ nguyên bar, không hạ.

Bài học: một con số 100% chỉ có nghĩa khi bộ đo chưa từng được dùng để sửa hệ thống. Từ giờ sẽ tách bộ đo ra trước khi
bắt đầu sửa, chứ không phải sau.

## Nếu làm lại tôi sẽ làm khác ở đâu

1. **Tách held-out ngay từ CP3.** Lúc Duy xây golden 27 case, nhẽ ra nhóm gom luôn 40 câu rồi cất 13 câu đi, chưa ai
   được đọc. Làm như vậy thì bar chốt ở CP4 mới có chỗ dựa thật, và nhóm không mất buổi tối 17/09 để chữa cháy.
2. **Đặt lịch validation trước, việc khác xếp sau.** Nhóm khai 2 willing user từ CP1 nhưng để phần đó đến sáng 18/09 mới
   tính, và cuối cùng không tổ chức được buổi thử nào. Đây là 8 điểm bonus nhóm mất, và mất vì không đặt lịch chứ không
   phải vì không có người.
3. **Không gộp commit theo checkpoint.** Tôi commit tập trung rồi squash cho gọn, nhưng làm thế thì lịch sử git không
   còn chứng minh được bar đã chốt trước khi chạy held-out, và cũng không thể hiện được ai làm phần nào. Lần sau mỗi
   người commit phần của mình.
