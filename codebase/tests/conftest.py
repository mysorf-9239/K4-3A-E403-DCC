"""Cấu hình pytest: dữ liệu và log nằm trong thư mục tạm, LLM được thay bằng hàm giả.

Biến ``DCC_DATA_DIR``/``DCC_LOG_DIR`` phải được đặt **trước** khi import ``dcc`` vì ``config`` đọc chúng lúc import.
"""
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

CODEBASE = Path(__file__).resolve().parent.parent
_TMP = Path(tempfile.mkdtemp(prefix="dcc-test-"))
(_TMP / "data").mkdir()
shutil.copy(CODEBASE / "data" / "registry.json", _TMP / "data" / "registry.json")
os.environ["DCC_DATA_DIR"] = str(_TMP / "data")
os.environ["DCC_LOG_DIR"] = str(_TMP / "logs")
os.environ["LLM_MAX_RPM"] = "0"
os.environ.pop("WEB_TA_TOKEN", None)
sys.path.insert(0, str(CODEBASE))

from dcc import config, decide  # noqa: E402


@pytest.fixture(autouse=True)
def clean_runtime() -> Iterator[None]:
    """Mỗi test bắt đầu với sổ nguồn gốc: xoá dữ liệu runtime và cache quyết định."""
    shutil.rmtree(config.RUNTIME_DIR, ignore_errors=True)
    config.RUNTIME_DIR.mkdir(parents=True)
    decide._CACHE.clear()
    yield


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, Any] | Exception], list[str]]:
    """Thay ``complete`` trong ``decide`` và ``ingest`` bằng hàm trả JSON cố định (hoặc ném lỗi).

    Returns:
        Hàm ``set_output(payload)``; trả list các user prompt đã gửi để test kiểm tra số lần gọi.
    """
    calls: list[str] = []

    def install(payload: dict[str, Any] | Exception) -> list[str]:
        """Cài hàm giả trả ``payload`` (hoặc ném lỗi) cho mọi lời gọi LLM."""

        def fake_complete(system: str, user: str) -> tuple[str, dict[str, Any]]:
            """Thay cho ``llm.complete``: ghi lại prompt và trả JSON cố định."""
            calls.append(user)
            if isinstance(payload, Exception):
                raise payload
            return json.dumps(payload, ensure_ascii=False), {"provider": "fake", "model": "fake"}

        monkeypatch.setattr("dcc.decide.complete", fake_complete)
        monkeypatch.setattr("dcc.ingest.complete", fake_complete)
        return calls

    return install
