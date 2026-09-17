"""Đọc/ghi file JSON an toàn khi bot Discord và web cùng chạy.

Mọi thao tác "đọc → sửa → ghi" dùng ``locked(path)``: khoá độc quyền qua file ``<tên>.lock`` (``fcntl.flock``)
để hai tiến trình không ghi đè dữ liệu của nhau. Ghi file dùng tệp tạm + ``os.replace`` để không bao giờ để lại
JSON ghi dở nếu tiến trình bị dừng giữa chừng.
"""
import fcntl
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


@contextmanager
def locked(path: Path) -> Iterator[None]:
    """Giữ khoá độc quyền cho ``path`` trong suốt khối ``with``.

    Args:
        path: File dữ liệu cần bảo vệ (khoá nằm ở ``path`` + ``.lock``).
    """
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def read_json(path: Path, default: Any) -> Any:
    """Đọc JSON; trả ``default`` nếu file chưa tồn tại."""
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    """Ghi JSON nguyên tử (tệp tạm rồi ``os.replace``)."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Thêm một dòng JSON vào file JSON Lines, có khoá."""
    with locked(path), path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Đọc file JSON Lines; bỏ qua dòng hỏng."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
