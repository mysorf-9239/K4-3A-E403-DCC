"""Test tiện ích cấu hình: nhận diện hạng mục tiếng Việt (lỗi B2) và múi giờ (lỗi B8)."""
from datetime import datetime

import pytest

from dcc import config


@pytest.mark.parametrize(("text", "expected"), [
    ("lab 3", ("lab", [3])),
    ("Bài lab", ("lab", None)),
    ("Đề tài nhóm", ("de_tai", None)),
    ("đề tài", ("de_tai", None)),
    ("daily standup", ("daily_standup", None)),
    ("daily_standup", ("daily_standup", None)),
    ("Mentor duty", ("mentor_duty", None)),
    ("CP3", ("hackathon_checkpoint", None)),
    ("thư viện", (None, None)),
])
def test_parse_item_supports_vietnamese(text: str, expected: tuple[str | None, list[int] | None]) -> None:
    """Chữ TA gõ (có dấu, không dấu, gạch dưới) được nhận đúng hạng mục; chữ lạ trả None thay vì đoán 'lab'."""
    assert config.parse_item(text) == expected


def test_now_is_naive_local_time() -> None:
    """``now()`` trả datetime không múi giờ theo APP_TIMEZONE, so sánh được với mốc giờ trong sổ nguồn."""
    assert isinstance(config.now(), datetime)
    assert config.now().tzinfo is None
