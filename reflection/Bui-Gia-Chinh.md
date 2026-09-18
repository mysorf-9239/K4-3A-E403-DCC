# Reflection — Bùi Gia Chính

AI Engineer nhóm DCC · 2A202602693 · lớp 3A, phòng E403, cụm C3

## Vai trò và phần việc của tôi

Tôi làm phần lõi trong [`codebase/dcc/`](../codebase/dcc/) — chỗ quyết định xem một câu hỏi sẽ được trả lời thế nào.

Cụ thể là bốn file. [`decide.py`](../codebase/dcc/decide.py) chứa prompt quyết định, phần đọc JSON model trả về, và hàm
`_guard` kiểm lại kết quả bằng chính sổ nguồn. [`registry.py`](../codebase/dcc/registry.py) là sổ nguồn có phiên bản:
một mục có thể thay thế mục cũ (`supersedes`), ghi đè cục bộ theo lab hoặc theo mốc (`overrides`), giới hạn phạm vi lớp
(`classes`), và hàm `find_conflicts` tìm các mục còn hiệu lực nói khác nhau về cùng một thứ. [`ingest.py`](../codebase/dcc/ingest.py)
là chiều ngược lại: AI đọc thông báo trong `#announcements` rồi đề xuất NEW/UPDATE/CONFLICT/DUPLICATE, nhưng phải trích
nguyên văn và mốc giờ phải parse được, nếu không thì đề xuất bị chặn. [`llm.py`](../codebase/dcc/llm.py) lo phần gọi
HTTP: giới hạn 14 request/phút ngay phía client để không ăn 429 lúc demo, thử lại tối đa 4 lần theo gợi ý "retry in Xs"
của provider, và tách riêng trường hợp hết quota ngày để không thử lại vô ích.

Chỗ tôi mất nhiều thời gian nhất không phải prompt, mà là `_guard`. Hiện có 14 nhãn guard, mỗi nhãn là một lần model làm
sai theo một kiểu và tôi phải chặn bằng code — bỏ nguồn model bịa ra, tự chuyển sang bản mới nhất khi model trích bản đã
bị thay thế, ép CONFLICT khi sổ thật sự có hai mốc chỏi nhau, hạ về NOT_FOUND khi không còn nguồn nào hợp lệ.

## AI đã hỗ trợ thế nào

Tôi dùng AI để viết khung file và viết docstring, và nhất là để **đọc ngược code của chính mình**. Sáng 17/09 tôi nhờ rà
lại toàn bộ `registry.py` với câu hỏi "chỗ nào thay đổi một mục có thể phá mục khác", và phát hiện lỗi mà tôi chắc chắn
sẽ không tự nhìn ra: khi TA gia hạn CP3, hàm ghi đè của tôi ghi lại cả cụm mốc checkpoint, làm mất luôn CP4 và CP5 khỏi
sổ. Một lệnh gia hạn tưởng là vô hại lại xoá hai hạn khác.

Chỗ tôi phải tự sửa lại nhiều nhất là prompt. AI viết prompt rất trơn nhưng hay thêm câu kiểu "hãy trả lời hữu ích và
thân thiện", còn cái tôi cần là luật cứng, đánh số, mỗi luật một hành vi kiểm được. Tôi viết lại
[`prompts/decide_system.md`](../codebase/dcc/prompts/decide_system.md) theo hướng đó, hiện là 9 quy tắc.

Và một điều tôi học được là **prompt không thay được code**. Luật số 8 của tôi nói thẳng: nếu sổ không nêu chi tiết
người ta hỏi thì trả NOT_FOUND. Model vẫn vi phạm ở case HO07. Những gì bắt buộc phải đúng thì tôi để `_guard` kiểm, còn
prompt chỉ để giảm số lần guard phải ra tay.

## Một lỗi của nhóm và điều tôi rút ra

Lỗi tôi chọn là **HO14** trong [`eval/heldout_results.md`](../eval/heldout_results.md). Câu hỏi là "Lab 3 lớp 3B hạn nộp
khi nào?", kỳ vọng FOUND theo TB-03. Model trả đúng — trace ghi rõ lý do "lớp 3B không có quy định riêng". Rồi guard
`conflict_detected` của tôi đổi nó thành CONFLICT.

Nguyên nhân: `find_conflicts` lúc đó chỉ so hạng mục và số lab. TB-07 là mốc riêng của lớp 3A, nhưng phạm vi đó tôi chỉ
viết trong trường `scope` dạng chữ cho người đọc, code không hề biết. Nên với code thì TB-03 và TB-07 là hai mốc chỏi
nhau, bất kể học viên học lớp nào.

Điều đáng nói là guard này **bắt đúng** ở cả 4 lượt golden — case H4c, lần nào model cũng tự chọn một bên và guard kéo
lại. Tôi tin nó vì nó đúng 4 lần liên tiếp. Chỉ cần đổi một chiều của câu hỏi, từ lớp 3A sang 3B, là nó sai.

Bài học của tôi: **guard chỉ đúng tới mức dữ liệu nó dựa vào đủ chi tiết**. Tôi đã viết một luật về phạm vi lớp trong
khi sổ nguồn không có trường nào mô tả phạm vi lớp. Tôi sửa bằng cách thêm `classes` vào mục nguồn và hai hàm
`classes_overlap` / `applies_to_class`, chứ không sửa bằng cách thêm câu vào prompt.

Chuyện này lặp lại lần nữa ở HO07 và lần đó tôi chưa chữa được: sổ không có trường nào nói daily standup áp dụng cho
buổi nào, nên tôi không có gì để kiểm bằng code, và luật prompt thì model bỏ qua. Case đó vẫn đang trượt và nhóm ghi
nguyên trong kết quả.

## Nếu làm lại tôi sẽ làm khác ở đâu

1. **Thiết kế schema sổ nguồn trước, guard sau.** Hai lỗi nặng nhất của tôi đều là guard suy đoán một thứ mà dữ liệu
   không ghi. Nếu tôi liệt kê trước "một mục nguồn cần mô tả được những chiều nào" — hạng mục, lab, lớp, phạm vi buổi
   học, hiệu lực từ ngày nào — thì cả HO14 lẫn HO07 đã không xảy ra.
2. **Mỗi guard phải kèm một case ngược dấu.** Tôi có test cho "guard bắt đúng mâu thuẫn", nhưng không có test cho "guard
   không được bắt khi hai mục khác phạm vi". Từ giờ viết guard nào thì viết luôn case nó *không* được kích hoạt.
3. **Không đợi đến lúc đo mới đọc lại code.** Lỗi gia hạn xoá mất CP4/CP5 nằm im trong repo gần một ngày và không có
   case nào trong golden chạm tới. Nó được tìm ra vì tôi ngồi rà, chứ không phải vì bộ đo bắt được.
