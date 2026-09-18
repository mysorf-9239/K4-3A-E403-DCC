"""Bot Discord "DCC" — tra cứu nơi nộp / cách nộp / hạn nộp có nguồn, chạy trong server test của nhóm.

Lệnh cho học viên:
    /ask question:<câu hỏi>        Hỏi nơi/cách/hạn nộp; bot trả embed kèm nguồn và nút phản hồi.
    /deadlines [hours]             Các hạn nộp sắp tới (mặc định 48 giờ), mỗi dòng kèm nguồn.
    /remind item [minutes_before]  Bật nhắc hạn qua DM cho một hạng mục (tự đăng ký).
    /remind-off [item]             Tắt nhắc hạn.
    /sources                       Xem các mục nguồn đang hiệu lực.
    Tag ``@DCC <câu hỏi>`` nếu ``ENABLE_MENTION=1``.

Lệnh cho TA (role ``TA_ROLE_NAME`` hoặc quyền Manage Server):
    /ta-queue                      Các cụm câu hỏi chưa có nguồn / đang mâu thuẫn.
    /ta-digest [hours]             Bản tin số liệu (không dùng LLM).
    /source-add text [url]         Nạp một thông báo / tài liệu công khai → AI đề xuất mục nguồn.
    Chuột phải tin nhắn → Apps → "Add to DCC sources".
    Tin mới trong kênh ``ANNOUNCE_CHANNEL_ID`` được tự động đưa vào đề xuất.

Luồng nạp nguồn:
    thông báo → ingest.propose() (LLM trích xuất + phân loại NEW/UPDATE/CONFLICT/DUPLICATE)
    → đăng đề xuất vào kênh TA → TA bấm Duyệt / Sửa rồi duyệt / Thay thế nguồn cũ / Giữ song song / Bỏ qua
    → registry.add_entry() → học viên hỏi lại nhận nguồn mới.

Luồng hàng chờ TA:
    NOT_FOUND / CONFLICT → gaps.add() gom cụm → đăng/cập nhật một tin trong kênh ``TA_CHANNEL_ID``
    → TA bấm "Duyệt thành nguồn" → form nhập nơi/cách/hạn nộp → registry.add_ta_entry() → cụm "resolved".

Biến môi trường: DISCORD_TOKEN (bắt buộc), DISCORD_GUILD_ID, TA_CHANNEL_ID, ANNOUNCE_CHANNEL_ID,
TA_ROLE_NAME (mặc định "TA"), ENABLE_MENTION (mặc định 1), BOT_NICKNAME (mặc định "DCC").

Chạy (từ thư mục ``codebase/``)::

    .venv/bin/python -m bot.discord_bot
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import discord
from discord import app_commands
from discord.ext import tasks

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dcc import config, digest, gaps, ingest, registry, reminders  # noqa: E402
from dcc.config import ITEMS, env  # noqa: E402
from dcc.decide import decide  # noqa: E402
from dcc.render import card, item_label, source_line  # noqa: E402

TOKEN = env("DISCORD_TOKEN")
GUILD_ID = env("DISCORD_GUILD_ID")
TA_CHANNEL_ID = int(env("TA_CHANNEL_ID", "0"))
ANNOUNCE_CHANNEL_ID = int(env("ANNOUNCE_CHANNEL_ID", "0"))
TA_ROLE_NAME = env("TA_ROLE_NAME", "TA")
ENABLE_MENTION = env("ENABLE_MENTION", "1") == "1"
BOT_NICKNAME = env("BOT_NICKNAME", "DCC")
QUEUE_DECISIONS = ("NOT_FOUND", "CONFLICT")


# ---------------------------------------------------------------- client

class DCCClient(discord.Client):
    """Client Discord kèm command tree; khi khởi động gắn lại nút duyệt, menu chuột phải và vòng nhắc hạn."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = ENABLE_MENTION or bool(ANNOUNCE_CHANNEL_ID)
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """Gắn lại view cho cụm/đề xuất đang mở (nút còn bấm được sau khi khởi động lại), đăng ký menu chuột phải,
        bật vòng nhắc hạn và đồng bộ slash command (theo guild nếu có ``DISCORD_GUILD_ID`` để hiện ngay)."""
        for gap in gaps.list_gaps("open"):
            self.add_view(GapView(gap["id"]))
        for proposal in ingest.list_proposals("pending"):
            self.add_view(ProposalView(proposal))
        self.tree.add_command(add_to_sources_menu)
        reminder_loop.start()
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()


client = DCCClient()


def is_ta(member: discord.abc.User) -> bool:
    """Người dùng có quyền TA không: có role ``TA_ROLE_NAME`` hoặc quyền Manage Server."""
    perms = getattr(member, "guild_permissions", None)
    if perms and perms.manage_guild:
        return True
    return any(role.name == TA_ROLE_NAME for role in getattr(member, "roles", []))


async def deny_if_not_ta(interaction: discord.Interaction, action: str) -> bool:
    """Từ chối (chỉ người bấm thấy) nếu không phải TA; trả ``True`` khi đã từ chối."""
    if is_ta(interaction.user):
        return False
    await interaction.response.send_message(f"Chỉ role **{TA_ROLE_NAME}** được {action}.", ephemeral=True)
    return True


# ---------------------------------------------------------------- answering

def build_embed(c: dict[str, Any], question: str) -> discord.Embed:
    """Dựng ``discord.Embed`` từ thẻ trả lời của ``render.card``; câu hỏi gốc hiển thị ở footer."""
    title = f"{c['label']} — {c['title']}" if c["title"] else c["label"]
    embed = discord.Embed(title=title[:256], description=(c["description"] or None), color=c["color"])
    for name, value in c["fields"]:
        embed.add_field(name=name[:256], value=value[:1024], inline=False)
    for s in c["sources"]:
        embed.add_field(name="📌 Nguồn", value=f"> {s['quote']}\n`{s['line']}`"[:1024], inline=False)
    if c["warning"]:
        embed.add_field(name="⚠️ Lưu ý", value=c["warning"][:1024], inline=False)
    if c["note"]:
        embed.add_field(name="ℹ️ Ghi chú", value=c["note"][:1024], inline=False)
    embed.set_footer(text=f"Hỏi: {question[:120]} · trace {c['trace_id']}")
    return embed


async def resolve_question(question: str, hint: dict[str, Any] | None,
                           channel: str) -> tuple[discord.Embed, "AnswerView"]:
    """Chạy ``decide`` ở thread riêng (không chặn event loop) và đưa NOT_FOUND/CONFLICT vào hàng chờ TA.

    Args:
        question: Câu hỏi học viên.
        hint: Lựa chọn đã bấm, ví dụ ``{"item": "lab", "lab": 3}``.
        channel: Nhãn kênh để ghi trace (``discord`` | ``discord-mention``).

    Returns:
        Embed và view trả lời sẵn để gửi.
    """
    d = await asyncio.to_thread(decide, question, hint, channel)
    c = card(d)
    if d["decision"] in QUEUE_DECISIONS:
        gap, is_new = gaps.add(question, d)
        await post_or_update_gap(gap, is_new)
        queued = f"📨 Đã vào hàng chờ TA **{gap['id']}** ({gap['count']} lượt hỏi cùng ý)."
        c["note"] = f"{c['note']} · {queued}" if c["note"] else queued
    return build_embed(c, question), AnswerView(question, d, c)


async def reply_followup(interaction: discord.Interaction, question: str, hint: dict[str, Any] | None = None) -> None:
    """Trả lời một interaction đã ``defer``: gửi embed công khai trong kênh."""
    embed, view = await resolve_question(question, hint, "discord")
    await interaction.followup.send(embed=embed, view=view)


# ---------------------------------------------------------------- student views

class ItemSelect(discord.ui.Select):
    """Menu chọn hạng mục (nhánh CLARIFY thiếu hạng mục, hoặc correction "Không phải cái tôi hỏi")."""

    def __init__(self, question: str) -> None:
        self.question = question
        options = [discord.SelectOption(label=label, value=key) for key, label in ITEMS.items()]
        super().__init__(placeholder="Chọn hạng mục bạn muốn hỏi", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        """Hỏi tiếp số lab nếu chọn "Bài lab"; ngược lại trả lời lại với hạng mục đã chọn."""
        item = self.values[0]
        if item == "lab":
            await interaction.response.send_message("Lab số mấy?", view=LabView(self.question), ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        await reply_followup(interaction, self.question, {"item": item})


class LabSelect(discord.ui.Select):
    """Menu chọn số lab 1–8 (nhánh CLARIFY thiếu số lab)."""

    def __init__(self, question: str) -> None:
        self.question = question
        options = [discord.SelectOption(label=f"Lab {i}", value=str(i)) for i in range(1, 9)]
        super().__init__(placeholder="Chọn lab", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        """Trả lời lại với ``{"item": "lab", "lab": n}``."""
        await interaction.response.defer(thinking=True)
        await reply_followup(interaction, self.question, {"item": "lab", "lab": int(self.values[0])})


class LabView(discord.ui.View):
    """View chỉ chứa ``LabSelect``."""

    def __init__(self, question: str) -> None:
        super().__init__(timeout=600)
        self.add_item(LabSelect(question))


class ItemView(discord.ui.View):
    """View chỉ chứa ``ItemSelect``."""

    def __init__(self, question: str) -> None:
        super().__init__(timeout=600)
        self.add_item(ItemSelect(question))


class ReasonSelect(discord.ui.Select):
    """Menu "Sai chỗ nào?" sau khi bấm 👎; ghi lý do vào feedback."""

    REASONS = ["Sai hạn nộp", "Sai nơi nộp", "Nguồn đã cũ", "Không phải cái tôi hỏi", "Khác"]

    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        super().__init__(placeholder="Sai chỗ nào?", options=[discord.SelectOption(label=r) for r in self.REASONS])

    async def callback(self, interaction: discord.Interaction) -> None:
        """Ghi lý do 👎 đã chọn vào feedback."""
        gaps.log_feedback(self.trace_id, "thumbs_down", self.values[0], "discord")
        await interaction.response.send_message(f"Đã ghi nhận: **{self.values[0]}**. Cảm ơn bạn!", ephemeral=True)


class AnswerView(discord.ui.View):
    """Nút dưới mỗi câu trả lời; chỉ hiện những nút có trong ``card["actions"]``.

    Nút: Không phải cái tôi hỏi (correction) · 👍 Hữu ích · 👎 Sai / thiếu · Soạn tin gửi TA/BTC (OUT_OF_SCOPE),
    cùng menu chọn hạng mục / số lab cho nhánh CLARIFY.
    """

    def __init__(self, question: str, d: dict[str, Any], c: dict[str, Any]) -> None:
        super().__init__(timeout=1800)
        self.question, self.d = question, d
        actions = set(c["actions"])
        if "pick_item" in actions:
            self.add_item(ItemSelect(question))
        if "pick_lab" in actions:
            self.add_item(LabSelect(question))
        if "wrong_item" not in actions:
            self.remove_item(self.wrong_item)
        if "thumbs_up" not in actions:
            self.remove_item(self.thumbs_up)
            self.remove_item(self.thumbs_down)
        if "ask_ta_manual" not in actions:
            self.remove_item(self.draft_to_ta)

    @discord.ui.button(label="Không phải cái tôi hỏi", emoji="✏️", style=discord.ButtonStyle.secondary)
    async def wrong_item(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        """Correction: ghi feedback rồi mở menu chọn lại hạng mục (chỉ người bấm thấy)."""
        gaps.log_feedback(self.d["trace_id"], "wrong_item", None, "discord")
        await interaction.response.send_message("Bạn muốn hỏi hạng mục nào?", view=ItemView(self.question),
                                                ephemeral=True)

    @discord.ui.button(label="Hữu ích", emoji="👍", style=discord.ButtonStyle.success)
    async def thumbs_up(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        """Ghi feedback tích cực."""
        gaps.log_feedback(self.d["trace_id"], "thumbs_up", None, "discord")
        await interaction.response.send_message("Cảm ơn bạn! 👍", ephemeral=True)

    @discord.ui.button(label="Sai / thiếu", emoji="👎", style=discord.ButtonStyle.danger)
    async def thumbs_down(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        """Mở menu chọn lý do sai."""
        view = discord.ui.View(timeout=600)
        view.add_item(ReasonSelect(self.d["trace_id"]))
        await interaction.response.send_message("Sai chỗ nào?", view=view, ephemeral=True)

    @discord.ui.button(label="Soạn tin gửi TA/BTC", emoji="📝", style=discord.ButtonStyle.secondary)
    async def draft_to_ta(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        """OUT_OF_SCOPE: soạn sẵn tin để học viên tự gửi — bot không gửi thay (non-goal)."""
        text = (f"Chào TA/BTC, em cần hỗ trợ: \"{self.question}\". "
                "Bot DCC báo việc này ngoài phạm vi tra cứu (gia hạn/điểm cá nhân). Em cảm ơn ạ.")
        await interaction.response.send_message(
            f"Bạn tự copy và gửi vào kênh hỗ trợ hoặc tạo ticket — DCC không gửi thay bạn:\n```{text}```",
            ephemeral=True)


# ---------------------------------------------------------------- TA queue

def gap_embed(gap: gaps.Gap) -> discord.Embed:
    """Embed hiển thị một cụm câu hỏi trong kênh TA (không chứa tên/ID người hỏi)."""
    color = {"resolved": 0x1F9D6B}.get(gap["status"], 0xE0A100 if gap["decision"] == "CONFLICT" else 0xC9443B)
    embed = discord.Embed(title=f"{gap['id']} · {gap['decision']} · {gap['count']} lượt hỏi", color=color)
    embed.add_field(name="Hạng mục", value=item_label(gap["item"], gap["lab"]) if gap["item"] else "Chưa rõ",
                    inline=True)
    embed.add_field(name="Chủ đề", value=gap["topic"] or "—", inline=True)
    if gap["source_ids"]:
        name = "Nguồn đang mâu thuẫn" if gap["decision"] == "CONFLICT" else "Nguồn liên quan"
        embed.add_field(name=name, value=", ".join(gap["source_ids"]), inline=False)
    questions = "\n".join(f"• {q[:150]}" for q in gap["questions"][-5:])
    embed.add_field(name="Các cách hỏi (ẩn danh)", value=questions[:1024], inline=False)
    if gap["status"] == "resolved":
        embed.add_field(name="✅ Đã duyệt", inline=False,
                        value=f"{gap.get('entry_id')} bởi {gap.get('resolved_by')} lúc {gap.get('resolved_at')}")
    embed.set_footer(text=f"Tạo {gap['created']} · cập nhật {gap['updated']}")
    return embed


def ta_channel() -> Any:
    """Kênh TA đã cấu hình (``discord.TextChannel``), hoặc ``None``."""
    return client.get_channel(TA_CHANNEL_ID) if TA_CHANNEL_ID else None


async def post_or_update_gap(gap: gaps.Gap, is_new: bool) -> None:
    """Đăng cụm mới vào kênh TA, hoặc sửa tin cũ để cập nhật số lượt hỏi. Bỏ qua nếu chưa cấu hình kênh."""
    channel = ta_channel()
    if channel is None:
        return
    if not is_new and gap.get("message_id"):
        try:
            msg = await channel.fetch_message(gap["message_id"])
            await msg.edit(embed=gap_embed(gap), view=GapView(gap["id"]))
            return
        except discord.NotFound:
            pass
    msg = await channel.send(embed=gap_embed(gap), view=GapView(gap["id"]))
    gaps.set_message_id(gap["id"], msg.id)


class ApproveGapModal(discord.ui.Modal, title="Duyệt thành nguồn"):
    """Form TA nhập câu trả lời chính thức cho một cụm."""

    item_lab = discord.ui.TextInput(label="Hạng mục (vd: lab 3, đề tài, daily standup)", max_length=40)
    where = discord.ui.TextInput(label="Nơi nộp", max_length=200)
    how = discord.ui.TextInput(label="Cách nộp", style=discord.TextStyle.paragraph, max_length=400)
    deadline = discord.ui.TextInput(label="Hạn nộp", max_length=120)
    who = discord.ui.TextInput(label="Ai nộp / lưu ý (không bắt buộc)", required=False, max_length=300)

    def __init__(self, gap: gaps.Gap) -> None:
        super().__init__()
        self.gap = gap
        self.item_lab.default = f"lab {gap['lab']}" if gap["lab"] else (gap["item"] or "")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Nhận diện hạng mục (hỗ trợ tiếng Việt), tạo ``TA-xx`` (thay nguồn mâu thuẫn nếu cụm CONFLICT), đóng cụm."""
        item, labs = config.parse_item(self.item_lab.value)
        if item is None:
            await interaction.response.send_message(
                f"Không nhận ra hạng mục '{self.item_lab.value}'. Dùng: lab <số>, đề tài, daily standup, "
                "mentor duty, checkpoint.", ephemeral=True)
            return
        supersedes = self.gap["source_ids"] if self.gap["decision"] == "CONFLICT" else None
        content = {"where": self.where.value, "how": self.how.value, "deadline": self.deadline.value,
                   "who": self.who.value}
        entry = registry.add_ta_entry(item, content, interaction.user.display_name, self.gap["questions"][0],
                                      labs, supersedes)
        gaps.resolve(self.gap["id"], entry["id"], interaction.user.display_name)
        await interaction.response.edit_message(embed=gap_embed(gaps.get(self.gap["id"])), view=None)
        replaced = f" Thay/ghi đè {', '.join(supersedes)}." if supersedes else ""
        await interaction.followup.send(f"✅ Đã thêm **{entry['id']}** ({item_label(item, (labs or [None])[0])}) "
                                        f"vào sổ nguồn.{replaced} Người hỏi sau sẽ nhận câu trả lời có nguồn.")


class GapView(discord.ui.View):
    """Nút "Duyệt thành nguồn" của một cụm; ``custom_id`` cố định để còn bấm được sau khi bot khởi động lại."""

    def __init__(self, gap_id: str) -> None:
        super().__init__(timeout=None)
        self.gap_id = gap_id
        button = discord.ui.Button(label="Duyệt thành nguồn", emoji="✅", style=discord.ButtonStyle.success,
                                   custom_id=f"dcc:approve:{gap_id}")
        button.callback = self.approve
        self.add_item(button)

    async def approve(self, interaction: discord.Interaction) -> None:
        """Kiểm tra quyền và trạng thái cụm rồi mở ``ApproveGapModal``."""
        if await deny_if_not_ta(interaction, "duyệt"):
            return
        gap = gaps.get(self.gap_id)
        if not gap or gap["status"] != "open":
            await interaction.response.send_message("Cụm này đã được xử lý.", ephemeral=True)
            return
        await interaction.response.send_modal(ApproveGapModal(gap))


# ---------------------------------------------------------------- source ingestion (TA)

RELATION_LABELS = {"NEW": "🆕 Nguồn mới", "UPDATE": "🔁 Cập nhật nguồn cũ",
                   "CONFLICT": "⚠️ Mâu thuẫn với nguồn đang có", "DUPLICATE": "♻️ Trùng nguồn đã có"}
RELATION_COLORS = {"NEW": 0x3B82F6, "UPDATE": 0x1F9D6B, "CONFLICT": 0xE0A100, "DUPLICATE": 0x6B7280}


def _proposal_result(p: ingest.Proposal) -> str:
    """Dòng kết quả sau khi TA xử lý đề xuất."""
    done = f"{p['status']} bởi {p.get('reviewer')} lúc {p.get('reviewed_at')}"
    if p.get("entry_id"):
        done += f" → `{p['entry_id']}`" + (" (thay thế nguồn cũ)" if p.get("replaced") else "")
        done += " · TA đã sửa nội dung" if p.get("edited") else ""
    return done


def proposal_embed(p: ingest.Proposal) -> discord.Embed:
    """Embed một đề xuất nguồn trong kênh TA: nội dung AI trích xuất, quan hệ với sổ, kiểm tra tự động, kết quả."""
    e = p["entry"]
    color = {"approved": 0x1F9D6B, "rejected": 0x6B7280}.get(p["status"], RELATION_COLORS[p["relation"]])
    embed = discord.Embed(title=f"{p['id']} · {RELATION_LABELS[p['relation']]}"[:256], color=color,
                          description=f"**{e['title']}** — {item_label(e['item'], (e.get('labs') or [None])[0])}")
    for name, key in (("Ai nộp", "who"), ("Nơi nộp", "where"), ("Cách nộp", "how"), ("Hạn nộp", "deadline")):
        embed.add_field(name=name, value=str(e.get(key))[:1024], inline=False)
    if e.get("deadlines"):
        embed.add_field(name="Mốc giờ đọc được", value=ingest.deadlines_to_text(e["deadlines"])[:1024], inline=False)
    if e.get("recurring_daily_close"):
        embed.add_field(name="Đóng mỗi ngày", value=e["recurring_daily_close"], inline=True)
    if p["related_ids"]:
        index = registry.by_id()
        related = "\n".join(f"`{i}` hạn: {index[i]['deadline']}" for i in p["related_ids"] if i in index)
        embed.add_field(name="Liên quan tới", value=related[:1024] or "—", inline=False)
    link = f" · {e['url']}" if e.get("url") else ""
    embed.add_field(name="📌 Trích dẫn", value=f"> {e['quote']}\n`{e['source']}{link}`"[:1024], inline=False)
    if p["guards"]:
        embed.add_field(name="Kiểm tra tự động", value=", ".join(p["guards"])[:1024], inline=False)
    if p["status"] != "pending":
        embed.add_field(name="Kết quả", value=_proposal_result(p), inline=False)
    embed.set_footer(text=f"AI đề xuất · TA quyết định · trace {p['trace_id']}")
    return embed


class EditProposalModal(discord.ui.Modal, title="Sửa rồi duyệt"):
    """Form TA sửa nội dung AI trích xuất trước khi ghi vào sổ nguồn."""

    where = discord.ui.TextInput(label="Nơi nộp", max_length=1000)
    how = discord.ui.TextInput(label="Cách nộp", style=discord.TextStyle.paragraph, max_length=2000)
    deadline = discord.ui.TextInput(label="Hạn nộp (chữ)", max_length=1000)
    who = discord.ui.TextInput(label="Ai nộp", required=False, max_length=1000)
    deadlines = discord.ui.TextInput(label="Mốc giờ: mỗi dòng 'nhãn | YYYY-MM-DDTHH:MM'", required=False,
                                     style=discord.TextStyle.paragraph, max_length=1000)

    def __init__(self, proposal: ingest.Proposal, replace: bool | None) -> None:
        super().__init__()
        self.proposal_id, self.replace = proposal["id"], replace
        e = proposal["entry"]
        # Discord từ chối mở form nếu giá trị mặc định dài hơn max_length → cắt cho vừa.
        for field, value in ((self.where, e["where"]), (self.how, e["how"]), (self.deadline, e["deadline"]),
                             (self.who, e["who"]), (self.deadlines, ingest.deadlines_to_text(e.get("deadlines")))):
            field.default = str(value or "")[: field.max_length]

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Duyệt với nội dung đã sửa; báo lỗi nếu mốc giờ sai định dạng."""
        edits = {"where": self.where.value, "how": self.how.value, "deadline": self.deadline.value,
                 "who": self.who.value, "deadlines": self.deadlines.value}
        try:
            ingest.approve(self.proposal_id, interaction.user.display_name, self.replace, edits)
        except ValueError as exc:
            await interaction.response.send_message(f"Chưa duyệt: {exc}", ephemeral=True)
            return
        await interaction.response.edit_message(embed=proposal_embed(ingest.get(self.proposal_id)), view=None)


class ProposalView(discord.ui.View):
    """Nút duyệt đề xuất nguồn; ``custom_id`` cố định theo mã đề xuất để còn bấm được sau khi khởi động lại.

    NEW → Duyệt · UPDATE → Duyệt (thay thế) · CONFLICT → Thay thế nguồn cũ / Giữ song song; trừ DUPLICATE đều có
    "Sửa rồi duyệt"; mọi loại có "Bỏ qua".
    """

    def __init__(self, proposal: ingest.Proposal) -> None:
        super().__init__(timeout=None)
        self.proposal_id = proposal["id"]
        relation = proposal["relation"]
        if relation in ("NEW", "UPDATE"):
            label = "Duyệt (thay thế nguồn cũ)" if relation == "UPDATE" else "Duyệt"
            self._button(label, "✅", discord.ButtonStyle.success, "approve", None)
        elif relation == "CONFLICT":
            self._button("Thay thế nguồn cũ", "🔁", discord.ButtonStyle.success, "replace", True)
            self._button("Giữ song song", "➕", discord.ButtonStyle.secondary, "parallel", False)
        if relation != "DUPLICATE":
            edit_replace = True if relation == "CONFLICT" else None
            self._button("Sửa rồi duyệt", "✏️", discord.ButtonStyle.primary, "edit", edit_replace)
        self._button("Bỏ qua", "✖️", discord.ButtonStyle.danger, "reject", None)

    def _button(self, label: str, emoji: str, style: discord.ButtonStyle, action: str, replace: bool | None) -> None:
        """Tạo một nút với ``custom_id`` dạng ``dcc:proposal:<action>:<id>``."""
        button = discord.ui.Button(label=label, emoji=emoji, style=style,
                                   custom_id=f"dcc:proposal:{action}:{self.proposal_id}")

        async def callback(interaction: discord.Interaction) -> None:
            """Chuyển lượt bấm sang ``handle`` với hành động của nút."""
            await self.handle(interaction, action, replace)

        button.callback = callback
        self.add_item(button)

    async def handle(self, interaction: discord.Interaction, action: str, replace: bool | None) -> None:
        """Kiểm tra quyền rồi duyệt / mở form sửa / bỏ qua và cập nhật tin nhắn."""
        if await deny_if_not_ta(interaction, "duyệt nguồn"):
            return
        proposal = ingest.get(self.proposal_id)
        if not proposal or proposal["status"] != "pending":
            await interaction.response.send_message("Đề xuất này đã được xử lý.", ephemeral=True)
            return
        if action == "edit":
            await interaction.response.send_modal(EditProposalModal(proposal, replace))
            return
        try:
            if action == "reject":
                ingest.reject(self.proposal_id, interaction.user.display_name)
            else:
                ingest.approve(self.proposal_id, interaction.user.display_name, replace)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.edit_message(embed=proposal_embed(ingest.get(self.proposal_id)), view=None)


async def ingest_and_post(text: str, source: str, url: str | None, channel_label: str,
                          message_id: int | None = None, published: str | None = None) -> dict[str, Any]:
    """Chạy ``ingest.propose`` ở thread riêng và đăng từng đề xuất vào kênh TA; trả kết quả ``propose``."""
    result = await asyncio.to_thread(ingest.propose, text, source, url, published, channel_label, message_id)
    channel = ta_channel()
    if channel:
        for p in result["proposals"]:
            msg = await channel.send(embed=proposal_embed(p), view=ProposalView(p))
            ingest.set_review_message(p["id"], msg.id)
    return result


def ingest_summary(result: dict[str, Any]) -> str:
    """Câu trả lời ngắn cho TA sau khi nạp."""
    if result["error"]:
        return "⚙️ Không gọi được AI: " + ("hết quota ngày." if result["error"] == "quota" else result["error"][:200])
    if not result["proposals"]:
        return "ℹ️ AI không thấy yêu cầu nộp bài nào trong nội dung này — không tạo đề xuất."
    ids = ", ".join(f"`{p['id']}` {p['relation']}" for p in result["proposals"])
    where = f"<#{TA_CHANNEL_ID}>" if TA_CHANNEL_ID else "kênh TA (chưa cấu hình TA_CHANNEL_ID)"
    return f"📥 Đã tạo {len(result['proposals'])} đề xuất: {ids}. Duyệt trong {where}."


def _published(message: discord.Message) -> str:
    """Thời điểm đăng tin nhắn theo giờ ``APP_TIMEZONE``, dạng ``YYYY-MM-DD HH:MM``."""
    return config.to_local(message.created_at).strftime("%Y-%m-%d %H:%M")


@app_commands.context_menu(name="Add to DCC sources")
async def add_to_sources_menu(interaction: discord.Interaction, message: discord.Message) -> None:
    """Menu chuột phải (TA): nạp một tin nhắn thông báo thành đề xuất nguồn."""
    if await deny_if_not_ta(interaction, "nạp nguồn"):
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    source = f"#{getattr(message.channel, 'name', 'discord')}"
    result = await ingest_and_post(message.content, source, message.jump_url, "discord-menu", message.id,
                                   _published(message))
    await interaction.followup.send(ingest_summary(result), ephemeral=True)


@client.tree.command(name="source-add", description="(TA) Nạp một thông báo / đoạn tài liệu công khai vào sổ nguồn")
@app_commands.describe(text="Nội dung thông báo", url="Link tới thông báo hoặc tài liệu gốc (nếu có)")
async def source_add(interaction: discord.Interaction, text: str, url: str | None = None) -> None:
    """Slash command nạp nguồn cho TA."""
    if await deny_if_not_ta(interaction, "nạp nguồn"):
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    result = await ingest_and_post(text, url or "Nội dung TA nạp", url, "discord-command")
    await interaction.followup.send(ingest_summary(result), ephemeral=True)


# ---------------------------------------------------------------- deadlines & reminders

ITEM_CHOICES = [app_commands.Choice(name=label, value=key) for key, label in ITEMS.items()]


def _relative(due: datetime) -> str:
    """Khoảng thời gian còn lại dạng "còn 3 giờ 20 phút"."""
    minutes = max(int((due - config.now()).total_seconds() // 60), 0)
    hours, mins = divmod(minutes, 60)
    return f"còn {hours} giờ {mins} phút" if hours else f"còn {mins} phút"


@client.tree.command(name="deadlines", description="Các hạn nộp sắp tới, kèm nguồn")
@app_commands.describe(hours="Nhìn trước bao nhiêu giờ (mặc định 48)")
async def deadlines(interaction: discord.Interaction, hours: app_commands.Range[int, 1, 336] = 48) -> None:
    """Liệt kê hạn tuyệt đối và hạn lặp mỗi ngày trong cửa sổ, mỗi dòng có mã nguồn."""
    items = registry.upcoming_deadlines(hours=hours)
    if not items:
        await interaction.response.send_message(f"Không có hạn nộp nào trong {hours} giờ tới theo sổ nguồn.",
                                                ephemeral=True)
        return
    lines = [f"**{d['due_at']:%H:%M %d/%m}** · {d['label']} · {_relative(d['due_at'])} · `{d['entry_id']}`"
             for d in items[:20]]
    embed = discord.Embed(title=f"⏰ Hạn nộp trong {hours} giờ tới", color=0x2F6FD6, description="\n".join(lines))
    embed.set_footer(text="Bài lab có hạn theo ngày học không hiển thị ở đây — dùng /ask. Bật nhắc: /remind")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.tree.command(name="remind", description="Bật nhắc hạn nộp qua tin nhắn riêng (tự đăng ký)")
@app_commands.describe(item="Hạng mục muốn nhắc", minutes_before="Nhắc trước hạn bao nhiêu phút (mặc định 120)")
@app_commands.choices(item=ITEM_CHOICES)
async def remind(interaction: discord.Interaction, item: app_commands.Choice[str],
                 minutes_before: app_commands.Range[int, 10, 1440] = 120) -> None:
    """Đăng ký nhắc hạn; báo trước hạn gần nhất sẽ được nhắc."""
    reminders.subscribe(interaction.user.id, item.value, minutes_before)
    upcoming = registry.upcoming_deadlines(hours=24 * 14, item=item.value)
    tail = (f" Hạn gần nhất: **{upcoming[0]['label']}** lúc {upcoming[0]['due_at']:%H:%M %d/%m} "
            f"(`{upcoming[0]['entry_id']}`)." if upcoming else " Sổ nguồn chưa có mốc giờ cụ thể cho hạng mục này.")
    await interaction.response.send_message(
        f"🔔 Đã bật nhắc **{item.name}** trước {minutes_before} phút qua tin nhắn riêng.{tail} Tắt: `/remind-off`.",
        ephemeral=True)


@client.tree.command(name="remind-off", description="Tắt nhắc hạn nộp")
@app_commands.describe(item="Hạng mục muốn tắt (bỏ trống = tắt tất cả)")
@app_commands.choices(item=ITEM_CHOICES)
async def remind_off(interaction: discord.Interaction, item: app_commands.Choice[str] | None = None) -> None:
    """Huỷ đăng ký nhắc hạn."""
    removed = reminders.unsubscribe(interaction.user.id, item.value if item else None)
    await interaction.response.send_message(f"🔕 Đã tắt {removed} đăng ký nhắc hạn.", ephemeral=True)


def reminder_embed(notice: dict[str, Any]) -> discord.Embed:
    """Embed DM nhắc hạn: mốc, nơi/cách nộp và nguồn."""
    d = notice["deadline"]
    embed = discord.Embed(title=f"⏰ Sắp hết hạn: {d['label']}"[:256], color=0xE0A100,
                          description=f"Hạn **{d['due_at']:%H:%M %d/%m}** ({notice['minutes_left']} phút nữa).")
    entry = registry.by_id().get(d["entry_id"])
    if entry:
        embed.add_field(name="Nơi nộp", value=entry["where"][:1024], inline=False)
        embed.add_field(name="Cách nộp", value=entry["how"][:1024], inline=False)
        embed.add_field(name="📌 Nguồn", value=source_line(entry)[:1024], inline=False)
    embed.set_footer(text="Bạn nhận tin này vì đã bật /remind. Tắt: /remind-off")
    return embed


@tasks.loop(seconds=60)
async def reminder_loop() -> None:
    """Mỗi phút: gửi DM cho các đăng ký có hạn nằm trong khoảng nhắc (mỗi mốc chỉ nhắc một lần)."""
    for notice in await asyncio.to_thread(reminders.due_notifications):
        try:
            user_id = int(notice["user_id"])
            user = client.get_user(user_id) or await client.fetch_user(user_id)
            await user.send(embed=reminder_embed(notice))
        except discord.HTTPException:
            await asyncio.to_thread(reminders.mark, notice["key"], False)
            continue
        await asyncio.to_thread(reminders.mark, notice["key"], True)


@reminder_loop.before_loop
async def _wait_ready() -> None:
    """Chờ bot đăng nhập xong mới chạy vòng nhắc."""
    await client.wait_until_ready()


@client.tree.command(name="ta-digest", description="(TA) Bản tin số liệu: câu hỏi, cụm cần xử lý, nguồn mới")
@app_commands.describe(hours="Nhìn lại bao nhiêu giờ (mặc định 24)")
async def ta_digest(interaction: discord.Interaction, hours: app_commands.Range[int, 1, 168] = 24) -> None:
    """Gửi bản tin số liệu (không dùng LLM) cho TA."""
    if await deny_if_not_ta(interaction, "xem bản tin"):
        return
    text = digest.to_markdown(digest.build(hours=hours))
    await interaction.response.send_message(embed=discord.Embed(description=text[:4000], color=0x2F6FD6),
                                            ephemeral=True)


# ---------------------------------------------------------------- student commands

@client.tree.command(name="ask", description="Hỏi nơi nộp / cách nộp / hạn nộp — trả lời kèm nguồn chính thức")
@app_commands.describe(question="Ví dụ: daily standup nộp ở đâu, hạn khi nào?")
async def ask(interaction: discord.Interaction, question: str) -> None:
    """Slash command chính của học viên."""
    await interaction.response.defer(thinking=True)
    await reply_followup(interaction, question)


@client.tree.command(name="sources", description="Xem các nguồn đang hiệu lực trong sổ nguồn")
async def sources(interaction: discord.Interaction) -> None:
    """Liệt kê mục ``active`` kèm loại nguồn (chỉ người gọi thấy)."""
    active = [e for e in registry.load_entries() if e["status"] == "active"]
    lines = [f"`{e['id']}` **{e['title']}** — hạn: {e['deadline']} ({source_line(e)})" for e in active]
    await interaction.response.send_message("\n".join(lines)[:1900] or "Sổ nguồn trống.", ephemeral=True)


@client.tree.command(name="ta-queue", description="(TA) Xem các cụm câu hỏi đang chờ xác nhận")
async def ta_queue(interaction: discord.Interaction) -> None:
    """Hiển thị tối đa 5 cụm đang mở, nhiều lượt hỏi nhất trước (chỉ TA)."""
    if await deny_if_not_ta(interaction, "xem hàng chờ"):
        return
    open_gaps = sorted(gaps.list_gaps("open"), key=lambda g: -g["count"])[:5]
    if not open_gaps:
        await interaction.response.send_message("Không có cụm nào đang chờ. 🎉", ephemeral=True)
        return
    await interaction.response.send_message(embed=gap_embed(open_gaps[0]), view=GapView(open_gaps[0]["id"]),
                                            ephemeral=True)
    for gap in open_gaps[1:]:
        await interaction.followup.send(embed=gap_embed(gap), view=GapView(gap["id"]), ephemeral=True)


# ---------------------------------------------------------------- events

def _strip_mention(content: str) -> str:
    """Bỏ phần tag bot khỏi nội dung tin nhắn."""
    for token in (f"<@{client.user.id}>", f"<@!{client.user.id}>"):
        content = content.replace(token, "")
    return content.strip()


@client.event
async def on_message(message: discord.Message) -> None:
    """Tin trong kênh thông báo → tự đưa vào đề xuất nguồn; tin tag bot → trả lời ``@DCC lab 2 nộp ở đâu?``."""
    if message.author.bot:
        return
    if ANNOUNCE_CHANNEL_ID and message.channel.id == ANNOUNCE_CHANNEL_ID and message.content.strip():
        await ingest_and_post(message.content, f"#{message.channel.name}", message.jump_url, "discord-auto",
                              message.id, _published(message))
        return
    if not ENABLE_MENTION or client.user not in message.mentions:
        return
    question = _strip_mention(message.content)
    if not question:
        await message.reply("Hỏi DCC về nơi nộp / cách nộp / hạn nộp nhé, ví dụ: "
                            "`/ask question: daily standup hạn khi nào?`")
        return
    async with message.channel.typing():
        embed, view = await resolve_question(question, None, "discord-mention")
    await message.reply(embed=embed, view=view)


@client.event
async def on_ready() -> None:
    """Đặt biệt danh ``BOT_NICKNAME`` trong từng server và in trạng thái khởi động."""
    for guild in client.guilds:
        if guild.me.nick != BOT_NICKNAME:
            try:
                await guild.me.edit(nick=BOT_NICKNAME)
            except discord.HTTPException:
                print(f"Không đổi được biệt danh trong {guild.name} (thiếu quyền Change Nickname)")
    print(f"Đăng nhập: {client.user} · LLM {config.LLM_PROVIDER}/{config.LLM_MODEL} · giờ {config.TIMEZONE} · "
          f"TA channel: {TA_CHANNEL_ID or 'chưa đặt'} · announce: {ANNOUNCE_CHANNEL_ID or 'chưa đặt'} · "
          f"role: {TA_ROLE_NAME}")


def main() -> None:
    """Điểm vào: kiểm tra token rồi chạy bot."""
    if not TOKEN:
        raise SystemExit("Thiếu DISCORD_TOKEN trong codebase/.env")
    client.run(TOKEN)


if __name__ == "__main__":
    main()
