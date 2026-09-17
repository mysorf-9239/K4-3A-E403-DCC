"""Web demo của DCC (bản dự phòng khi pitch) — dùng chung lõi ``dcc`` với bot Discord.

Endpoint học viên:
    GET  /                            Giao diện (tab Học viên + tab TA).
    GET  /api/meta                    Provider/model đang dùng và danh sách hạng mục.
    POST /api/ask                     ``{"question", "hint": {"item", "lab"} | null}``.
    POST /api/feedback                ``{"trace_id", "label", "detail"}``.
    GET  /api/deadlines?hours=48      Hạn nộp sắp tới.
    GET  /api/registry                Sổ nguồn hiện tại.
Endpoint TA (cần quyền TA, xem ``require_ta``):
    GET  /api/gaps · POST /api/gaps/{id}/approve
    POST /api/ingest · GET /api/proposals · POST /api/proposals/{id}/approve · POST /api/proposals/{id}/reject
    GET  /api/digest?hours=24

Quyền TA: nếu đặt ``WEB_TA_TOKEN`` thì request phải gửi header ``X-TA-Token`` khớp; nếu không đặt, chỉ chấp nhận
request từ máy chạy server (127.0.0.1 / ::1) — đủ cho demo local, không mở thao tác duyệt ra mạng.

Chạy (từ thư mục ``codebase/``)::

    .venv/bin/uvicorn web.app:app --port 8000
"""
import hmac
import sys
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dcc import config, digest, gaps, ingest, registry  # noqa: E402
from dcc.decide import decide  # noqa: E402
from dcc.render import card  # noqa: E402

app = FastAPI(title="DCC")
HERE = Path(__file__).resolve().parent
LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}


def require_ta(request: Request, x_ta_token: str | None = Header(default=None)) -> None:
    """Dependency kiểm tra quyền TA.

    Raises:
        HTTPException: 401 khi token sai/thiếu (có ``WEB_TA_TOKEN``), 403 khi gọi từ máy khác (không có token).
    """
    expected = config.env("WEB_TA_TOKEN")
    if expected:
        if not x_ta_token or not hmac.compare_digest(x_ta_token, expected):
            raise HTTPException(401, "Thiếu hoặc sai X-TA-Token")
        return
    host = request.client.host if request.client else ""
    if host not in LOCAL_HOSTS:
        raise HTTPException(403, "Thao tác TA chỉ cho phép từ máy chạy server (hoặc đặt WEB_TA_TOKEN)")


class AskBody(BaseModel):
    """Yêu cầu hỏi: câu hỏi và lựa chọn đã bấm (nếu có)."""

    question: str = Field(min_length=1, max_length=1000)
    hint: dict[str, Any] | None = None


class FeedbackBody(BaseModel):
    """Phản hồi cho một lượt trả lời."""

    trace_id: str
    label: str
    detail: str | None = None


class ApproveGapBody(BaseModel):
    """Nội dung TA nhập khi duyệt một cụm."""

    item: str
    lab: int | None = None
    where: str = Field(min_length=1)
    how: str = Field(min_length=1)
    deadline: str = Field(min_length=1)
    who: str = ""
    ta_name: str = "TA demo"


class IngestBody(BaseModel):
    """Thông báo TA muốn nạp."""

    text: str = Field(min_length=1, max_length=4000)
    source: str = "Nội dung TA nạp (web)"
    url: str | None = None


class ReviewBody(BaseModel):
    """Quyết định của TA với đề xuất nguồn; ``edits`` gồm who/where/how/deadline/deadlines nếu TA sửa."""

    replace: bool | None = None
    reviewer: str = "TA demo"
    edits: dict[str, str] | None = None


@app.get("/")
def index() -> FileResponse:
    """Trả trang ``index.html``."""
    return FileResponse(HERE / "index.html")


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    """Thông tin model để hiển thị trên header (chứng minh đang dùng AI thật)."""
    return {"provider": config.LLM_PROVIDER, "model": config.LLM_MODEL, "items": config.ITEMS,
            "ta_token_required": bool(config.env("WEB_TA_TOKEN"))}


@app.post("/api/ask")
def ask(body: AskBody) -> dict[str, Any]:
    """Chạy quyết định, dựng thẻ, đưa NOT_FOUND/CONFLICT vào hàng chờ TA; trả ``{"decision", "card", "gap"}``."""
    d = decide(body.question.strip(), body.hint, "web")
    gap = gaps.add(body.question, d)[0] if d["decision"] in ("NOT_FOUND", "CONFLICT") else None
    return {"decision": d, "card": card(d), "gap": gap}


@app.post("/api/feedback")
def feedback(body: FeedbackBody) -> dict[str, bool]:
    """Ghi phản hồi 👍/👎/sửa hạng mục."""
    gaps.log_feedback(body.trace_id, body.label, body.detail, "web")
    return {"ok": True}


@app.get("/api/deadlines")
def deadlines(hours: int = 48) -> list[dict[str, Any]]:
    """Hạn nộp sắp tới trong ``hours`` giờ."""
    return [{**d, "due_at": d["due_at"].strftime("%Y-%m-%d %H:%M")} for d in registry.upcoming_deadlines(hours=hours)]


@app.get("/api/registry")
def get_registry() -> list[dict[str, Any]]:
    """Sổ nguồn hiện tại (đã áp dụng mục runtime và đánh dấu thay thế)."""
    return registry.load_entries()


@app.get("/api/gaps", dependencies=[Depends(require_ta)])
def list_gaps() -> list[dict[str, Any]]:
    """Danh sách cụm: đang mở trước, nhiều lượt hỏi trước."""
    return sorted(gaps.list_gaps(None), key=lambda g: (g["status"] != "open", -g["count"]))


@app.post("/api/gaps/{gap_id}/approve", dependencies=[Depends(require_ta)])
def approve_gap(gap_id: str, body: ApproveGapBody) -> dict[str, Any]:
    """TA duyệt cụm thành mục ``TA-xx``; cụm CONFLICT thay/ghi đè các nguồn đang mâu thuẫn.

    Raises:
        HTTPException: 404 nếu cụm không tồn tại/đã đóng, 400 nếu hạng mục không hợp lệ.
    """
    gap = gaps.get(gap_id)
    if not gap or gap["status"] != "open":
        raise HTTPException(404, "Không có cụm đang mở")
    if body.item not in config.ITEMS:
        raise HTTPException(400, f"Hạng mục không hợp lệ: {body.item}")
    supersedes = gap["source_ids"] if gap["decision"] == "CONFLICT" else None
    content = {"where": body.where, "how": body.how, "deadline": body.deadline, "who": body.who}
    entry = registry.add_ta_entry(body.item, content, body.ta_name, gap["questions"][0],
                                  [body.lab] if body.lab else None, supersedes)
    gaps.resolve(gap_id, entry["id"], body.ta_name)
    return {"entry": entry}


@app.post("/api/ingest", dependencies=[Depends(require_ta)])
def ingest_notice(body: IngestBody) -> dict[str, Any]:
    """AI trích xuất thông báo thành đề xuất nguồn (chưa ghi vào sổ cho tới khi TA duyệt)."""
    return ingest.propose(body.text, body.source, body.url, channel="web")


@app.get("/api/proposals", dependencies=[Depends(require_ta)])
def proposals() -> list[dict[str, Any]]:
    """Mọi đề xuất nguồn, đang chờ trước."""
    return sorted(ingest.list_proposals(None), key=lambda p: (p["status"] != "pending", p["id"]))


@app.post("/api/proposals/{proposal_id}/approve", dependencies=[Depends(require_ta)])
def approve_proposal(proposal_id: str, body: ReviewBody) -> dict[str, Any]:
    """Duyệt đề xuất thành mục nguồn ``SRC-xx`` (có thể kèm nội dung TA sửa).

    Raises:
        HTTPException: 400 nếu đề xuất không hợp lệ để duyệt hoặc mốc giờ sửa sai định dạng.
    """
    try:
        return {"entry": ingest.approve(proposal_id, body.reviewer, body.replace, body.edits)}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/proposals/{proposal_id}/reject", dependencies=[Depends(require_ta)])
def reject_proposal(proposal_id: str, body: ReviewBody) -> dict[str, bool]:
    """Bỏ qua đề xuất."""
    ingest.reject(proposal_id, body.reviewer)
    return {"ok": True}


@app.get("/api/digest", dependencies=[Depends(require_ta)])
def get_digest(hours: int = 24) -> dict[str, str]:
    """Bản tin số liệu cho TA."""
    return {"markdown": digest.to_markdown(digest.build(hours=hours))}
