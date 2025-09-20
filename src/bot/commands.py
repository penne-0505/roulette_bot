"""Slashコマンドの登録処理。"""
from __future__ import annotations

import datetime
import time
from types import SimpleNamespace
from typing import TYPE_CHECKING

import discord
import psutil
from discord.app_commands import locale_str

from data_interface import FlowController
from db_manager import DBManager
from models.context_model import CommandContext
from models.model import SelectionMode
from models.state_model import AmidakujiState
from views.view import ModeSelectionView

if TYPE_CHECKING:  # pragma: no cover - 型チェック専用
    from .client import BotClient


def register_commands(client: "BotClient") -> None:
    """BotClientにスラッシュコマンドを紐付ける。"""

    tree = client.tree

    def require_db_manager(interaction: discord.Interaction) -> DBManager:
        db_manager = getattr(interaction.client, "db", None)
        if db_manager is None:
            raise RuntimeError("DB manager is not available")
        return db_manager

    @tree.command(name=locale_str("ping"), description="Ping the bot. 🏓")
    async def command_ping(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        ws_latency = round(client.latency * 1000)

        start_time = time.perf_counter()
        message = await interaction.followup.send("測定中...")
        end_time = time.perf_counter()
        api_latency = round((end_time - start_time) * 1000)

        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024
        cpu_usage = process.cpu_percent()

        embed = discord.Embed(
            title="🏓 Pong!", color=discord.Color.green(), timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name="📡 Connection",
            value=(
                "```\n"
                f"Websocket: {ws_latency}ms\n"
                f"API: {api_latency}ms\n"
                "```"
            ),
            inline=False,
        )

        embed.add_field(
            name="🤖 Status",
            value=(
                f"```\n"
                f"サーバー数: {len(client.guilds)}\n"
                f"ユーザー数: {len(client.users)}\n"
                f"```"
            ),
            inline=False,
        )

        uptime_s = time.time() - client.start_time
        uptime_m = int(uptime_s / 60)
        uptime_h = int(uptime_m / 60)

        embed.add_field(
            name="💻 System",
            value=(
                f"```\n"
                f"メモリ使用量: {memory_usage:.2f}MB\n"
                f"CPU使用率: {cpu_usage:.2f}%\n"
                f"稼働時間: {uptime_s:.2f}s "
                f"({uptime_h}h {uptime_m}m {uptime_s}s)\n"
                "```"
            ),
            inline=False,
        )

        try:
            await message.edit(embed=embed, content=None)
        except discord.NotFound:
            await interaction.followup.send(embed=embed, content=None)
        except Exception:  # pragma: no cover - Discord APIの例外は環境依存
            embed = discord.Embed(
                title="エラーが発生しました🥲",
                description="ping-Unknown-Exception",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(),
            )
            await interaction.followup.send(embed=embed, content=None, ephemeral=True)

    @tree.command(
        name=locale_str("amidakuji"),
        description="Assign roles to users randomly.",
    )
    async def command_amidakuji(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)
        services = SimpleNamespace(db=db_manager)
        context = CommandContext(
            interaction=interaction,
            state=AmidakujiState.COMMAND_EXECUTED,
            services=services,
        )

        flow = FlowController(context=context, services=services)
        services.flow = flow
        context.result = interaction

        view = ModeSelectionView(context=context)

        await interaction.followup.send(view=view, ephemeral=True)

    @tree.command(
        name=locale_str("toggle_embed_mode"),
        description="Toggle the embed mode of the result of the command.",
    )
    async def command_toggle_embed_mode(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)

        db_manager.toggle_embed_mode()
        current_mode = db_manager.get_embed_mode()

        embed = discord.Embed(
            title="埋め込みメッセージの表示形式を変更しました",
            description=f"現在の表示形式: {current_mode}",
            color=discord.Color.green(),
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @tree.command(
        name=locale_str("amidakuji_selection_mode"),
        description="抽選のアルゴリズムを切り替えます。",
    )
    @discord.app_commands.describe(mode="抽選モードを選択します。")
    @discord.app_commands.choices(
        mode=[
            discord.app_commands.Choice(
                name="完全ランダム", value=SelectionMode.RANDOM.value
            ),
            discord.app_commands.Choice(
                name="偏り軽減", value=SelectionMode.BIAS_REDUCTION.value
            ),
        ]
    )
    async def command_set_selection_mode(
        interaction: discord.Interaction, mode: discord.app_commands.Choice[str]
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)

        try:
            selection_mode = SelectionMode(mode.value)
        except ValueError as error:  # pragma: no cover - バリデーション用
            raise RuntimeError("Invalid selection mode") from error

        db_manager.set_selection_mode(selection_mode)

        embed = discord.Embed(
            title="抽選モードを更新しました",
            description=f"現在のモード: {mode.name}",
            color=discord.Color.green(),
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @tree.command(
        name=locale_str("amidakuji_history"),
        description="最近の抽選履歴を表示します。",
    )
    @discord.app_commands.describe(
        limit="表示件数 (1-10)", template_title="絞り込みたいテンプレート名 (任意)"
    )
    async def command_amidakuji_history(
        interaction: discord.Interaction,
        limit: int = 5,
        template_title: str | None = None,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)

        limit = max(1, min(10, limit))

        guild_id = interaction.guild_id or 0
        histories = db_manager.get_recent_history(
            guild_id=guild_id, template_title=template_title, limit=limit
        )

        if not histories:
            description = "抽選履歴が見つかりませんでした。"
            if template_title:
                description += f" (テンプレート: {template_title})"
            embed = discord.Embed(
                title="🎲 最近の抽選履歴",
                description=description,
                color=discord.Color.blue(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="🎲 最近の抽選履歴",
            description="最新の抽選結果を表示します。",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        for history in histories:
            try:
                selection_mode_label = {
                    SelectionMode.RANDOM: "完全ランダム",
                    SelectionMode.BIAS_REDUCTION: "偏り軽減",
                }[history.selection_mode]
            except KeyError:  # pragma: no cover - 想定外のモード
                selection_mode_label = history.selection_mode.value

            timestamp_text = history.created_at.astimezone(
                datetime.timezone.utc
            ).strftime("%Y-%m-%d %H:%M UTC")
            lines = [
                f"{entry.user_name} → {entry.choice}" for entry in history.entries
            ]
            field_value = "\n".join(lines) if lines else "記録がありません"
            if len(field_value) > 1024:
                field_value = field_value[:1010] + "\n..."

            field_name = (
                f"{history.template_title} ({timestamp_text}) [{selection_mode_label}]"
            )
            embed.add_field(name=field_name, value=field_value, inline=False)

        if template_title:
            embed.set_footer(text=f"テンプレート: {template_title}")

        await interaction.followup.send(embed=embed, ephemeral=True)


__all__ = ["register_commands"]
