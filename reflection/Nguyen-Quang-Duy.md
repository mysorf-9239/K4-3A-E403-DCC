# Reflection — Nguyễn Quang Duy

Research & Eval nhóm DCC · 2A202602426 · lớp 3A, phòng E403, cụm C3

## Vai trò và phần việc của tôi
Vai trò : Research & Eval

Trong nhóm, mình phụ trách phần Research Và Eval. Phần chính mình làm là xây dựng bộ dữ liệu để kiểm tra bot va theo dõi kết quả mỗi lần chạy.
Mình làm file [`eval/golden_set.json`](../eval/golden_set.json) gồm 27 case. Trong đó có 15 câu lấy từ tin nhắn thật trong `discord-pack`, mình giữ lại `msg_id` để sau này cần thì có thể tìm lại câu hỏi gốc. Các case còn lại mình tự thêm để kiểm tra trình huống khác nhau mà bot có thể gặp.
Mỗi case, mình ghi rõ bot cần trả lời như thế nào, nguồn nào bắt buộc phải có và nguồn nào không được dùng. Sau đó [`run_eval.py`](../eval/run_eval.py) sẽ dự vào những thông tin này để tự chấm kết quả thay vì phải kiểm tra từng câu bằng tay.
VỚi 15 câu hỏi thật, mình cũng thêm câu trả lời cũ của bot Kute vào `kute_baseline`. Mình kiểm tra xem Kute có trả lời được không, có dẫn nguồn không, có hỏi lại hay chuyển Mod không. Kết quả này được nhóm dùng để làm số liệu so sánh trong slide.
Ngoài golden set, mình làm thêm bộ 10 thông báo để test việc nạp nguồn, chạy [`run_ingest_eval.py`](../eval/run_ingest_eval.py) và lưu kết quả các lần chạy. Mình cũng viết bộ test pytest với LLM giả, hiện có 56 test, và chuẩn bị kịch bản hco phần user testing trong [`validation/user_testing_log.md`](../validation/user_testing_log.md).
Nói tóm lại, phần việc của mình chủ yếu là chuẩn bị dữ liệu, chạy test và kiểm tra xe bot đang hoạt động đúng đến đâu, sau đó ghi lại kết quả để nhóm dùng khi đánh giá hệ thống.

## AI đã hỗ trợ thế nào

Mình dùng AI chủ yếu ở 2 phần, nhưng phần nào mình cũng kiểm tra và chỉnh lại bằng tay, có rà soát lại.

Thứ nhất là sinh case. Mình đưa các tin nhắn thật cho AI rồi nhờ tạo thêm các biến thể. Tuy nhiên, nhiều biến thể AI tạo ra khá giống nhau, chủ yếu chỉ thay đổi cách diễn đạt chứ không tạo ra tình huống mới. Vì vậy, mình bỏ bớt những case bị trùng và viết lại dựa trên bốn nhóm tình huống khó, để mỗi case kiểm tra một vấn đề khác nhau.

Thứ hai là script chấm kết quả. Ai giúp mình viết `run_eval.py`, nhưng bản đầu chấm hơi dễ vì chỉ kiểm tra loại quyết định. Mình sửa lại kiểm tra thêm danh sách nguồn và thêm `forbid_sources`. Sau khi sửa, số case đạt tụt xuống, nhưng kết quả phản ánh đúng hơn chất lượng của bot. 
Ngoài ra, mình cũng dùng AI để hỗ trợ viết 56 test với LLM giả. Phần này khá ổn vì đầu vào và đầu ra đều được cố định, nên không phụ thuộc vào việc AI tự đoán két quả. 

## Một lỗi của nhóm và điều tôi rút ra

Lỗi mình chọn là lỗi của bộ đo: **golden set 27 case đạt 100% bốn lượt liên tiếp, nhưng bộ held-out 22 câu
chỉ đạt 19/22 = 86,4% và trượt quality bar.**

Kết quả trả về 27/27 khá yên tâm, nhưng sau khi trưởng nhóm viết bộ held-out và chạy thử, ba case bị trượt từ đó nhận ra vấn đề không hẳn nằm ở model, mà nằm ở bộ đo.

- **HO14** (Lab 3 lớp **3B**) - trong 27 case của mình, các câu hỏi về Lab 3 đều là lớp 3A. Mình chưa có case nào để đổi lớp,    nên guard mâu thuẫn nhìn như đúng trong cả bốn lượt, nhưng thực tế lại không kiểm tra được các lớp khác 
- **HO07** (daily standup áp dụng cho buổi LAB/LEC hay chỉ build phase) - Mình chưa có case nào hỏi về phạm vi áp dụng của một quy định. 27 case trước đó chủ yếu hỏi về ở đâu, làm như thế nào hoặc hạn khi nào.
- **HO22** (câu hỏi quy định nộp bài lẫn trong một tin toàn lỗi kỹ thuật) - Có E01 khá giống, nhưng ở E01 phần hỏi về nộp được viết rõ hơn nên case đó dễ hơn tình huống thực tế.

Nói tóm lại là bộ đo của mình đạt 100%, nhưng hệ thống chưa chắc đúng. Bộ case mình tạo chưa đủ nhiều dạng để kiểm tra. Trong quá trình làm, prompt và guard cũng được sửa nhiều lần dựa trên 27 case đó nên dần dần hệ thống phù hợp với bộ đo hơn. Đây là vấn đề overfit bộ đo.

Điều mình rút ra: bộ đo phải có nhiều dạng tình huống và không nên chỉ dùng những case đã dùng để chỉnh hệ thống. Các case cần thay đổi nhiều chiều như lớp, lab, các cách hỏi và mục đích thực sự của người dùng.

## Nếu làm lại tôi sẽ làm khác ở đâu

1. **Chia đôi bộ case ngay từ đầu.** Chia bộ case thành hai phần ngay từ đầu. Ví dụ có 40 câu thì giữ lại 13 câu làm held-out và không dùng những câu đó để chỉnh hệ thống cho đến khi chốt quality bar.
2. **Dựng case theo lưới, không theo cảm tính.** Lập bảng gồm các yếu tô như hạng mục, lớp, lab có/không có trong sổ, cách viết và ý định của người dùng. Sau đó chọn case từ từng nhóm.
3. **Tách lỗi hạ tầng khỏi lỗi mô hình ngay từ lượt đầu.** Lượt golden 1 có case E01 trượt chỉ vì lỗi 429 hết quota. Về sau `run_eval.py` đếm riêng "lỗi gọi LLM".

S