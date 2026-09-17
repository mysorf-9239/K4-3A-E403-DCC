"""Lõi bot DCC — tra cứu nơi nộp / cách nộp / hạn nộp có nguồn cho học viên AI20k (nhóm DCC, Track B1).

Module:
    config: đọc ``.env``, đường dẫn dữ liệu, danh sách hạng mục.
    registry: sổ nguồn có phiên bản (tài liệu công khai, thông báo giả lập, nguồn nạp/TA duyệt), mâu thuẫn, hạn sắp tới.
    llm: gọi LLM thật (Gemini / OpenAI / Anthropic) qua HTTP, có thử lại.
    decide: quyết định trung tâm FOUND / CONFLICT / CLARIFY / NOT_FOUND / OUT_OF_SCOPE + guard + trace.
    gaps: hàng chờ TA gom cụm, log phản hồi.
    render: thẻ trả lời dùng chung cho Discord và web.
    ingest: AI trích xuất thông báo thành đề xuất nguồn (NEW / UPDATE / CONFLICT / DUPLICATE) cho TA duyệt.
    reminders: nhắc hạn nộp tự đăng ký.
    digest: bản tin số liệu cho TA (không dùng LLM).
"""
