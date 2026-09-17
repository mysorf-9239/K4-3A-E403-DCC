"""Cấu hình dùng chung cho bot Discord, web demo, script eval và test.

Mọi giá trị đọc từ biến môi trường, ưu tiên file ``codebase/.env`` (không commit). Module cũng tạo sẵn thư mục
runtime/log khi được import.

Biến môi trường:
    LLM_PROVIDER: ``gemini`` (mặc định) | ``openai`` | ``anthropic``.
    LLM_MODEL: tên model; bỏ trống thì dùng ``DEFAULT_MODELS[LLM_PROVIDER]``.
    LLM_MAX_RPM: số request/phút tối đa phía client (mặc định 14, dưới giới hạn 15 của Gemini free tier).
    GEMINI_THINKING_LEVEL: mức suy luận cho Gemini 3.x (``minimal`` | ``low`` | ``medium`` | ``high``).
    GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY: key của provider đang dùng.
    APP_TIMEZONE: múi giờ tính hạn nộp (mặc định ``Asia/Ho_Chi_Minh``), độc lập với giờ của máy chạy.
    DCC_DATA_DIR / DCC_LOG_DIR: đổi thư mục dữ liệu/log (dùng trong test).
"""
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

CODEBASE = Path(__file__).resolve().parent.parent
load_dotenv(CODEBASE / ".env")


def env(name: str, default: str = "") -> str:
    """Đọc biến môi trường, coi chuỗi rỗng như chưa khai báo.

    Args:
        name: Tên biến.
        default: Giá trị trả về khi biến không có hoặc rỗng.

    Returns:
        Giá trị đã bỏ khoảng trắng hai đầu, hoặc ``default``.
    """
    value = os.getenv(name, "").strip()
    return value or default


DATA_DIR = Path(env("DCC_DATA_DIR", str(CODEBASE / "data")))
RUNTIME_DIR = DATA_DIR / "runtime"
LOG_DIR = Path(env("DCC_LOG_DIR", str(CODEBASE / "logs")))
REGISTRY_FILE = DATA_DIR / "registry.json"

RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LLM_PROVIDER = env("LLM_PROVIDER", "gemini").lower()
DEFAULT_MODELS = {
    "gemini": "gemini-3.5-flash-lite",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}
LLM_MODEL = env("LLM_MODEL", DEFAULT_MODELS.get(LLM_PROVIDER, ""))
LLM_MAX_RPM = int(env("LLM_MAX_RPM", "14"))
GEMINI_THINKING_LEVEL = env("GEMINI_THINKING_LEVEL", "low")
TIMEZONE = ZoneInfo(env("APP_TIMEZONE", "Asia/Ho_Chi_Minh"))

#: Hạng mục nộp bài được hỗ trợ → nhãn hiển thị cho học viên.
ITEMS = {
    "daily_standup": "Daily standup",
    "lab": "Bài lab",
    "de_tai": "Đề tài nhóm",
    "mentor_duty": "Mentor duty",
    "hackathon_checkpoint": "Checkpoint Mini Hackathon",
}

#: Từ khoá (không dấu) nhận diện hạng mục khi TA gõ tay.
_ITEM_KEYWORDS = [
    ("daily_standup", r"daily|standup|stand up"),
    ("mentor_duty", r"mentor"),
    ("de_tai", r"de tai|detai|topic|de_tai"),
    ("hackathon_checkpoint", r"checkpoint|hackathon|\bcp\s*\d"),
    ("lab", r"\blab\b|\blab\s*\d|bai lab"),
]


def now() -> datetime:
    """Thời điểm hiện tại theo ``APP_TIMEZONE``, dạng naive (so sánh được với mốc giờ trong sổ nguồn)."""
    return datetime.now(TIMEZONE).replace(tzinfo=None)


def to_local(value: datetime) -> datetime:
    """Đổi một datetime có múi giờ (ví dụ ``message.created_at`` của Discord) sang giờ ``APP_TIMEZONE`` naive."""
    return value.astimezone(TIMEZONE).replace(tzinfo=None)


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt và viết thường, ví dụ "Đề tài" → "de tai"."""
    decomposed = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def parse_item(text: str) -> tuple[str | None, list[int] | None]:
    """Nhận diện hạng mục và số lab từ chữ TA gõ, hỗ trợ tiếng Việt có dấu.

    Args:
        text: Ví dụ ``"lab 3"``, ``"Đề tài nhóm"``, ``"daily_standup"``, ``"CP3"``.

    Returns:
        ``(item, labs)``; ``item`` là ``None`` nếu không nhận ra. ``labs`` chỉ có khi là bài lab kèm số.
    """
    plain = strip_accents(text).replace("_", " ").strip()
    for item, pattern in _ITEM_KEYWORDS:
        if re.search(pattern, plain):
            digits = re.findall(r"\d+", plain) if item == "lab" else []
            return item, ([int(d) for d in digits] or None)
    key = plain.replace(" ", "_")
    return (key, None) if key in ITEMS else (None, None)
