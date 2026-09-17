"""Lớp gọi LLM thật qua HTTP cho ba provider: Gemini, OpenAI, Anthropic.

Không dùng SDK để giữ ít phụ thuộc. Mọi provider nhận cùng ``(system, user)`` và trả văn bản JSON thô; việc parse
và kiểm tra nằm ở ``decide.py`` / ``ingest.py``.

Bảo vệ quota:
    * **Giới hạn phía client** ``LLM_MAX_RPM`` request/phút (mặc định 14): request vượt ngưỡng sẽ *chờ* thay vì
      bị provider trả 429 — quan trọng khi nhiều người hỏi cùng lúc lúc demo.
    * Lỗi mạng, HTTP 500/502/503 và 429 theo phút → thử lại tối đa 4 lần, chờ theo gợi ý "retry in Xs" của
      provider (nếu không có thì 2s, 4s, 6s, 8s).
    * 429 hết quota theo ngày → không thử lại, ném ``QuotaExceeded``.
"""
import os
import re
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Any

import httpx

from . import config

TIMEOUT = 60
MAX_RETRIES = 4

ProviderResult = tuple[str, dict[str, Any]]


class LLMError(RuntimeError):
    """Lỗi khi gọi provider (thiếu key, HTTP lỗi, phản hồi không đúng định dạng)."""


class QuotaExceeded(LLMError):
    """Provider báo hết quota không phục hồi trong phiên (ví dụ giới hạn request/ngày của free tier)."""


class RateLimiter:
    """Giới hạn số lời gọi trong cửa sổ trượt 60 giây, an toàn đa luồng (bot gọi LLM trong thread pool)."""

    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max_per_minute
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> float:
        """Chờ tới khi được phép gọi; trả số giây đã phải chờ."""
        waited = 0.0
        while True:
            with self._lock:
                current = time.monotonic()
                while self._calls and current - self._calls[0] >= 60:
                    self._calls.popleft()
                if self.max_per_minute <= 0 or len(self._calls) < self.max_per_minute:
                    self._calls.append(current)
                    return waited
                delay = 60 - (current - self._calls[0]) + 0.1
            time.sleep(delay)
            waited += delay


LIMITER = RateLimiter(config.LLM_MAX_RPM)


def _raise_for(provider: str, response: httpx.Response) -> None:
    """Chuyển phản hồi HTTP lỗi thành ``LLMError`` / ``QuotaExceeded`` kèm nội dung để ghi trace."""
    body = response.text[:1200]
    if response.status_code == 429 and "PerDay" in body:
        raise QuotaExceeded(f"{provider} 429 (hết quota ngày): {body}")
    raise LLMError(f"{provider} {response.status_code}: {body}")


def _require_key(name: str) -> str:
    """Lấy API key hoặc báo lỗi rõ ràng."""
    key = os.getenv(name)
    if not key:
        raise LLMError(f"Thiếu {name} trong codebase/.env")
    return key


def _gemini(system: str, user: str) -> ProviderResult:
    """Gọi Gemini ``generateContent`` (JSON mode, nhiệt độ 0); bỏ phần ``thought`` khỏi đầu ra."""
    generation: dict[str, Any] = {"temperature": 0, "responseMimeType": "application/json", "maxOutputTokens": 1024}
    if config.LLM_MODEL.startswith("gemini-3"):
        generation["thinkingConfig"] = {"thinkingLevel": config.GEMINI_THINKING_LEVEL}
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": generation}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.LLM_MODEL}:generateContent"
    r = httpx.post(url, params={"key": _require_key("GEMINI_API_KEY")}, json=body, timeout=TIMEOUT)
    if r.status_code != 200:
        _raise_for("Gemini", r)
    data = r.json()
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought")), data.get("usageMetadata", {})


def _openai(system: str, user: str) -> ProviderResult:
    """Gọi OpenAI Chat Completions với ``response_format=json_object``, nhiệt độ 0."""
    body = {"model": config.LLM_MODEL, "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    headers = {"Authorization": f"Bearer {_require_key('OPENAI_API_KEY')}"}
    r = httpx.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, timeout=TIMEOUT)
    if r.status_code != 200:
        _raise_for("OpenAI", r)
    data = r.json()
    return data["choices"][0]["message"]["content"], data.get("usage", {})


def _anthropic(system: str, user: str) -> ProviderResult:
    """Gọi Anthropic Messages API, nhiệt độ 0; ghép các khối ``text``."""
    body = {"model": config.LLM_MODEL, "max_tokens": 1024, "temperature": 0, "system": system,
            "messages": [{"role": "user", "content": user}]}
    headers = {"x-api-key": _require_key("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01"}
    r = httpx.post("https://api.anthropic.com/v1/messages", json=body, headers=headers, timeout=TIMEOUT)
    if r.status_code != 200:
        _raise_for("Anthropic", r)
    data = r.json()
    return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text"), data.get("usage", {})


PROVIDERS: dict[str, Callable[[str, str], ProviderResult]] = {
    "gemini": _gemini, "openai": _openai, "anthropic": _anthropic,
}


def _transient(exc: Exception) -> bool:
    """Lỗi có nên thử lại không: lỗi mạng, 5xx tạm thời, hoặc 429 không phải hết quota ngày."""
    if isinstance(exc, QuotaExceeded):
        return False
    if isinstance(exc, httpx.TransportError):
        return True
    return any(f" {code}:" in str(exc) for code in (429, 500, 502, 503))


def _retry_delay(exc: Exception, attempt: int) -> float:
    """Số giây chờ trước lần thử lại: theo gợi ý "retry in Xs" của provider nếu có, không thì 2s × lần thử."""
    match = re.search(r"retry in ([\d.]+)s", str(exc))
    return float(match.group(1)) + 1 if match else 2.0 * attempt


def complete(system: str, user: str) -> ProviderResult:
    """Gọi provider đang cấu hình, có giới hạn tốc độ và thử lại với lỗi tạm thời.

    Args:
        system: System prompt.
        user: Nội dung người dùng.

    Returns:
        ``(raw_text, meta)`` với ``meta`` gồm provider, model, số lần thử lại, thời gian chờ giới hạn, độ trễ (ms)
        và thông tin token do provider trả về.

    Raises:
        QuotaExceeded: Hết quota ngày.
        LLMError: Lỗi còn lại sau khi đã thử lại.
    """
    fn = PROVIDERS.get(config.LLM_PROVIDER)
    if not fn:
        raise LLMError(f"LLM_PROVIDER không hỗ trợ: {config.LLM_PROVIDER}")
    start = time.time()
    retries, throttled = 0, 0.0
    while True:
        throttled += LIMITER.acquire()
        try:
            text, usage = fn(system, user)
            break
        except (LLMError, httpx.TransportError) as exc:
            if not _transient(exc) or retries >= MAX_RETRIES:
                raise
            retries += 1
            time.sleep(_retry_delay(exc, retries))
    return text, {"provider": config.LLM_PROVIDER, "model": config.LLM_MODEL, "retries": retries,
                  "throttled_s": round(throttled, 1), "latency_ms": int((time.time() - start) * 1000), "usage": usage}
