# Khảo sát trải nghiệm tìm thông tin và hỏi đáp trên Discord AI20k

## Bộ câu hỏi thực tế đã phát trên Google Form (10 câu)

Lấy nguyên văn từ header dữ liệu xuất [survey-raw.csv](survey-raw.csv). Kết quả: [survey-results.md](survey-results.md).

1. Trong 7 ngày qua, bạn đã cần tìm thông tin hoặc hỏi đáp trên Discord khóa học bao nhiêu lần?
2. Lần gần nhất, bạn cần tìm thông tin thuộc nhóm nào?
3. Kể ngắn gọn lần đó: bạn cần biết điều gì hoặc hoàn thành việc gì?
4. Bạn đã làm những gì để tìm câu trả lời trong lần đó?
5. Trở ngại lớn nhất trong lần đó là gì?
6. Bạn đã dành khoảng bao lâu chủ động tìm, đọc hoặc hỏi trong lần đó?
7. Cuối cùng, bạn có giải quyết được việc cần làm không?
8. Việc tìm thông tin lần đó ảnh hưởng thế nào đến việc học/làm bài?
9. Riêng trong lần đó, bạn có dùng bot Trợ lý Discord không? Kết quả thế nào?
10. Trong 7 ngày qua, trở ngại tương tự đã xảy ra bao nhiêu lần?

Form thực tế **không** gồm các câu đồng ý/đối tượng/đăng ký thử (Q1–Q3, Q13–Q15 của bản thiết kế bên dưới); người thử
được xác nhận riêng ngoài form.

---

## Bản thiết kế ban đầu (tham khảo, không phải form đã phát)

## Mô tả hiển thị đầu form

Nhóm DCC đang tìm hiểu cách học viên tìm thông tin và giải quyết câu hỏi trong khóa AI20k. Khảo sát khoảng 4–6 phút, hỏi
về trải nghiệm đã xảy ra; không có câu trả lời đúng/sai. Bạn chưa gặp khó khăn cũng là thông tin hữu ích. Chỉ gửi một
lần; không gửi mật khẩu, điểm cá nhân, ảnh chụp hoặc nội dung riêng tư của người khác.

Nhóm giữ bản trả lời gốc và thông tin nhận diện ở nơi riêng tư để đối chiếu; báo cáo dùng mã người trả lời, số liệu tổng
hợp và trích dẫn đã loại thông tin nhận diện. Đăng ký dùng thử là tự nguyện, tách khỏi việc xác nhận vấn đề.

## Cấu hình Google Forms

- Không dùng chế độ quiz; không hiển thị bản tổng hợp câu trả lời cho người tham gia.
- Giữ thứ tự câu hỏi. Không bắt thu email tự động; dùng mã khảo sát để chống đếm trùng.
- Nhóm phát mã S001, S002… và giữ bảng đối chiếu người thật riêng tư. Phân bổ mã theo người phỏng vấn để không cấp
  trùng; kiểm tra cùng một học viên không được hai mã.
- A: Đồng ý và xác định đối tượng. Q1 không đồng ý hoặc Q2 là thành viên DCC/không phải học viên → kết thúc, không tính
  mẫu.
- B: Trải nghiệm. Q4 = 0 lần → chuyển phần D (đăng ký thử), vẫn giữ trong mẫu hợp lệ với trạng thái chưa gặp nhu cầu.
- C: Chi tiết lần gần nhất dành cho Q4 khác 0. D: đăng ký thử tự nguyện. Q13 chọn Có → phần E liên hệ, chọn Không/Chưa
  chắc → gửi form.
- Q1–Q13 bắt buộc ở nhánh tương ứng; luôn giữ các lựa chọn không nhớ/không gặp. Q14–Q15 chỉ bắt buộc với người chủ động
  chọn Có ở Q13.

## Phần A — Đối tượng

**Q1. Bạn đồng ý tham gia theo mô tả trên không?** — Trắc nghiệm: Đồng ý / Không đồng ý.

**Q2. Bạn thuộc nhóm nào?** — Trắc nghiệm: Học viên AI20k ngoài nhóm DCC / Thành viên DCC / Không phải học viên AI20k.

**Q3. Mã khảo sát do nhóm cung cấp và lớp của bạn?** — Trả lời ngắn, ví dụ định dạng `S___ — 3A`. Không yêu cầu mã học
viên, số điện thoại ở câu này.

## Phần B — Tần suất

**Q4. Trong 7 ngày qua, bạn đã cần tìm thông tin hoặc hỏi đáp liên quan khóa học trên Discord bao nhiêu lần?** — Trắc
nghiệm: 0 / 1 / 2–3 / 4–6 / 7 trở lên / Có nhưng không nhớ số lần.

## Phần C — Một tình huống đã xảy ra

**Q5. Lần gần nhất là khi nào và bạn cần biết hoặc làm được việc gì?** — Đoạn văn. Nếu không nhớ, ghi “không nhớ”; không
cần chép tin nhắn của người khác.

**Q6. Thông tin lần đó thuộc loại nào?** — Trắc nghiệm: Hạn/link/cách nộp bài / Điểm danh–standup–XP–thủ tục / Kiến thức
hoặc lỗi khi làm bài / Lịch học–thông báo / Khác / Không nhớ.

**Q7. Bạn đã làm những bước nào, theo thứ tự, để tìm câu trả lời? Cuối cùng bạn dựa vào đâu để biết câu trả lời dùng
được?** — Đoạn văn. Ghi đúng việc đã làm; nếu chưa tìm được thì nói rõ.

**Q8. Lần đó, bạn gặp những tình huống nào?** — Hộp kiểm: Không gặp trở ngại / Không tìm thấy thông báo hoặc link cần
dùng / Thông tin khác nhau và chưa biết áp dụng cho lớp/bài nào / Câu hỏi chưa được giải đáp đủ để tiếp tục / Câu trả
lời khó hiểu hoặc không có căn cứ để kiểm tra / Khác / Không nhớ. Hướng dẫn: “Không gặp trở ngại” và “Không nhớ” không
chọn cùng các đáp án khác.

**Q9. Bạn đã dành khoảng bao nhiêu phút chủ động tìm/đọc/hỏi trong lần đó? Nếu có chờ phản hồi, ghi riêng thời gian
chờ.** — Trả lời ngắn. Cho phép 0 và “không nhớ”; không cộng thời gian chờ vào thời gian thao tác.

**Q10. Lần đó kết thúc thế nào và ảnh hưởng thực tế đến việc học/làm bài của bạn ra sao?** — Đoạn văn. Nếu không có ảnh
hưởng, ghi rõ; không yêu cầu phải có hậu quả tiêu cực.

**Q11. Riêng trong lần đó, bạn có dùng bot Trợ lý Discord không?** — Trắc nghiệm: Không dùng / Có, trả lời đủ và tôi
tiếp tục được / Có, tôi phải hỏi lại hoặc tìm nguồn khác / Có, chưa nhận được câu trả lời / Không nhớ.

**Q12. Trong 7 ngày qua, trở ngại tương tự đã xảy ra bao nhiêu lần? Hãy nêu ngắn gọn trở ngại bạn đang đếm.** — Trả lời
ngắn. Cho phép “0 — không gặp”, hoặc “không nhớ”.

## Phần D — Mời dùng thử (không tính là bằng chứng nỗi đau)

**Q13. Bạn có đồng ý dành khoảng 10 phút dùng thử bản mẫu của nhóm trước 13:00 ngày 18/09/2026 không?** — Trắc nghiệm:
Có / Chưa chắc / Không.

## Phần E — Chỉ hiện nếu Q13 = Có

**Q14. Họ tên và một cách liên hệ thuận tiện (Discord hoặc email)?** — Trả lời ngắn. Chỉ để nhóm hẹn thử; không đưa
thông tin liên hệ lên repo công khai.

**Q15. Bạn có thể thử vào khung giờ nào trước hạn trên, và đồng ý để nhóm khai tên bạn là người dùng thử với BTC ở CP1
không?** — Đoạn văn. Nếu chưa đồng ý khai tên hoặc chưa chốt thời gian, nhóm cần liên hệ xác nhận trước khi đưa vào CP1.

## Gợi ý hỏi tiếp trực tiếp

- “Bạn nói khó tìm: lần gần nhất bạn tìm ở đâu trước, rồi làm gì tiếp?”
- “Thông tin đó khác nhau cụ thể thế nào? Bạn đã kiểm lại bằng cách nào?”
- “Sau khi chờ, bạn có tiếp tục được bài không?”
- “Bạn không gặp khó khăn: cách nào đang giúp bạn làm việc này thuận lợi?”

Không giới thiệu giải pháp trước khi hỏi. Không hỏi “bạn có cần chatbot AI không?”. Giữ nguyên câu trả lời gốc; phần
nhóm diễn giải hoặc gắn nhãn đặt ở cột riêng.
