# Evidence chuẩn B — mining `discord-pack` (lượt 1, 16/09/2026)

Nguồn: `data/discord-pack/k4_messages.csv` của repo đề (1.092 tin, 12–14/09/2026, 2 server K4). Data pack **không**
commit vào repo này; chỉ dẫn `msg_id` và trích ≤2 câu.

## Phương pháp đếm

1. Chỉ lấy tin của người: `is_bot == False` → **779 tin**.
2. Là câu hỏi: nội dung có `?` hoặc một trong các cụm
   `không ạ|ko ạ|k ạ|sao|thế nào|như nào|ở đâu|khi nào|bao giờ|hỏi|được không` (không phân biệt hoa thường) → **275
   tin**.
3. Liên quan yêu cầu nộp: nội dung khớp regex `nộp|submit|deadline|hạn` → 33 tin.
4. Đọc tay, loại 5 tin không phải hỏi về yêu cầu nộp của học viên: M41530 (thông báo BTC), M34960 (xếp hạng XP), M80377
   (giấy tờ NVQS), M44168 (CV doanh nghiệp), M16662 (deadline feedback video của studio).
5. Kết quả: **28 câu hỏi** về cách/nơi/hạn nộp, từ **18 tác giả khác nhau**. Đây là số lượng tin hỏi, không phải số
   người trong toàn khóa.

Script tái lập (chạy trong `data/discord-pack/` của repo đề):

```python
import csv, re

rows = list(csv.DictReader(open('k4_messages.csv')))
ex = {'M41530', 'M34960', 'M80377', 'M44168', 'M16662'}
isq = lambda t: '?' in t or re.search(r'(không ạ|ko ạ|k ạ|sao|thế nào|như nào|ở đâu|khi nào|bao giờ|hỏi|được không)',
                                      t.lower())
sub = [r for r in rows if r['is_bot'] == 'False' and isq(r['content'])
       and re.search(r'(nộp|submit|deadline|hạn)', r['content'], re.I) and r['msg_id'] not in ex]
print(len(sub), len({r['author'] for r in sub}))  # 28 18
```

## Số đếm

| Chỉ số                                          | Giá trị                                                                |
|-------------------------------------------------|------------------------------------------------------------------------|
| Câu hỏi về yêu cầu nộp / tổng câu hỏi của người | 28 / 275 (10,2%) trong 3 ngày                                          |
| Số tác giả khác nhau                            | 18                                                                     |
| Trong đó hỏi trực tiếp bot (`mentions_bot`)     | 21 / 28                                                                |
| Hỏi về daily standup                            | 15 tin, 9 tác giả                                                      |
| Nhắc đến nộp muộn / bị chặn / xin gia hạn       | 8 tin (M88027, M01360, M21463, M32784, M98666, M45316, M82163, M35080); **7 đã xảy ra** (6 tác giả), M35080 là câu hỏi giả định |
| Trong 7 tin đã xảy ra: do không rõ/nhầm khung giờ | 5 (M98666, M82163, M45316, M21463, M32784) — đọc tay; M88027 muộn 1 phút, M01360 lỡ cửa sổ lập đội |
| Phân bố theo ngày                               | 12/09: 1 · 13/09: 12 · 14/09: 15                                       |

Nhận xét: cùng một câu hỏi (nộp daily standup ở đâu/như thế nào/khi nào) lặp lại nhiều lần trong buổi sáng 14/09
(M57734, M79664, M65205, M81080, M78574), dù đã có thông báo và bot. Nhiều người hỏi lại sau khi đã nhận câu trả lời của
bot (M58536, M76564, M15491, M60145 trích lại câu bot rồi hỏi tiếp).

## Ví dụ nguyên văn (≥5)

1. **M57734** — "[@BOT] quy cách nộp daily standup, cả nhóm có phải nộp ko? hình thức nộp như nào, viết ra sao, có mẫu
   ko? Nộp vào đâu?"
2. **M65205** — "[@BOT] nộp ở đâu cơ, phần này mình đánh lệnh /daily-standup rồi mà ko được"
3. **M98666** — "[@BOT] thời gian mở daily standup và kết thúc là khi nào vậy? hôm qua mình gửi sớm daily standup thì
   không được, chiều nay quá deadline thì nó lại blocked mình."
4. **M82163** — "[@BOT] cái daly-standup sao m ghi là hết hôm nay nhưng nộp bài thì m kêu hết hạn."
5. **M88027** — "cho em hỏi Lab2 có được extend thời gian submit thêm không v ạ? Em lỡ nộp muộn 1 phút không submit bài
   được ạ"
6. **M21463** — "dạ cho em hỏi là hôm nay em mới nộp daily standup, em nhận được thông báo là em nộp muộn không được
   điểm danh..."
7. **M91752** — "[@BOT] mình có thể nộp đề tài nhóm mình chọn ở đâu"

## Giới hạn

- Chỉ 3 ngày onboarding, chỉ kênh public; không suy ra tỷ lệ toàn khóa.
- Regex có thể bỏ sót câu hỏi không dùng từ "nộp/hạn" (ví dụ hỏi về điểm danh). Số 28 là cận dưới.
- M82163 cho thấy câu trả lời của bot có thể mâu thuẫn với hệ thống thực tế; chưa kiểm chứng nguồn chính thức.
- Kết quả khảo sát Google Form (chuẩn A) ở [survey-results.md](survey-results.md).
