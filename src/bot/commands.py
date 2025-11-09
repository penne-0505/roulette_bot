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
from domain.interfaces.repositories import TemplateRepository
from domain import ResultEmbedMode, SelectionMode, Template, TemplateScope
from domain.services.template_service import merge_templates
from models.context_model import CommandContext
from models.state_model import AmidakujiState
from views.embed_mode import (
    EmbedModeView,
    create_embed_mode_overview_embed,
)
from views.selection_mode import (
    SelectionModeView,
    create_selection_mode_overview_embed,
)
from views.template_management import TemplateManagementView
from views.history_list import HistoryListView
from views.template_list import TemplateListView
from views.template_sharing import TemplateSharingView
from views.view import ModeSelectionView

if TYPE_CHECKING:  # pragma: no cover - 型チェック専用
    from .client import BotClient


def register_commands(client: "BotClient") -> None:
    """BotClientにスラッシュコマンドを紐付ける。"""

    tree = client.tree

    def require_db_manager(interaction: discord.Interaction) -> TemplateRepository:
        db_manager = getattr(interaction.client, "db", None)
        if db_manager is None:
            raise RuntimeError("DB manager is not available")
        return db_manager

    @tree.command(
        name=locale_str("ping"),
        description=locale_str("ping.description"),
    )
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

        uptime_s = round(time.time() - client.start_time, 2)
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
        description=locale_str("amidakuji.description"),
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
        name=locale_str("amidakuji_template_create"),
        description=locale_str("amidakuji_template_create.description"),
    )
    async def command_create_template(interaction: discord.Interaction) -> None:
        db_manager = require_db_manager(interaction)
        services = SimpleNamespace(db=db_manager)
        context = CommandContext(
            interaction=interaction,
            state=AmidakujiState.MODE_CREATE_NEW,
            services=services,
        )

        flow = FlowController(context=context, services=services)
        services.flow = flow
        context.result = interaction

        await flow.dispatch(
            AmidakujiState.MODE_CREATE_NEW,
            interaction,
            interaction,
        )

    @tree.command(
        name=locale_str("amidakuji_template_manage"),
        description=locale_str("amidakuji_template_manage.description"),
    )
    async def command_manage_templates(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)
        user_id = interaction.user.id
        user = db_manager.get_user(user_id, include_shared=False)

        templates = user.custom_templates if user else []
        if not templates:
            embed = discord.Embed(
                title="テンプレートはまだありません",
                description="まずは `/amidakuji_template_create` でテンプレートを作成してください。",
                color=discord.Color.orange(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        view = TemplateManagementView(
            db_manager=db_manager,
            user_id=user_id,
            templates=templates,
        )

        await interaction.followup.send(
            embed=view.create_embed(),
            view=view,
            ephemeral=True,
        )

    @tree.command(
        name=locale_str("toggle_embed_mode"),
        description=locale_str("toggle_embed_mode.description"),
    )
    async def command_toggle_embed_mode(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)
        raw_mode = db_manager.get_embed_mode()
        try:
            current_mode = ResultEmbedMode(str(raw_mode))
        except ValueError:  # pragma: no cover - 不正値は初期値へフォールバック
            current_mode = ResultEmbedMode.COMPACT

        embed = create_embed_mode_overview_embed(current_mode)
        view = EmbedModeView(
            db_manager=db_manager,
            current_mode=current_mode,
            user_id=interaction.user.id,
        )

        await interaction.followup.send(
            embed=embed,
            view=view,
            ephemeral=True,
        )

    @tree.command(
        name=locale_str("amidakuji_template_list"),
        description=locale_str("amidakuji_template_list.description"),
    )
    async def command_list_templates(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)
        user_id = interaction.user.id
        guild_id = interaction.guild_id

        user = db_manager.get_user(user_id, guild_id=guild_id, include_shared=True)

        if user is not None:
            private_templates = list(user.custom_templates)
            guild_templates = list(user.shared_templates)
            public_templates = list(user.public_templates)
        else:
            guild_templates, public_shared = db_manager.get_shared_templates_for_user(
                guild_id=guild_id
            )
            default_templates = db_manager.get_default_templates()
            private_templates = []
            public_templates = merge_templates(public_shared, default_templates)

        view = TemplateListView(
            private_templates=private_templates,
            guild_templates=guild_templates,
            public_templates=public_templates,
        )

        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @tree.command(
        name=locale_str("amidakuji_selection_mode"),
        description=locale_str("amidakuji_selection_mode.description"),
    )
    async def command_set_selection_mode(
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)

        raw_mode = db_manager.get_selection_mode()
        if isinstance(raw_mode, SelectionMode):
            current_mode = raw_mode
        else:
            try:
                current_mode = SelectionMode(str(raw_mode))
            except ValueError:  # pragma: no cover - 不正値は初期値へフォールバック
                current_mode = SelectionMode.RANDOM

        embed = create_selection_mode_overview_embed(current_mode)
        view = SelectionModeView(
            db_manager=db_manager,
            current_mode=current_mode,
            user_id=interaction.user.id,
        )

        await interaction.followup.send(
            embed=embed,
            view=view,
            ephemeral=True,
        )

    @tree.command(
        name=locale_str("amidakuji_history"),
        description=locale_str("amidakuji_history.description"),
    )
    async def command_amidakuji_history(
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)

        limit = 5
        guild_id = interaction.guild_id or 0

        view = HistoryListView(
            db_manager=db_manager,
            guild_id=guild_id,
            page_size=limit,
            template_title=None,
        )

        embed = view.create_embed()

        await interaction.followup.send(
            embed=embed,
            view=view,
            ephemeral=True,
        )

    @tree.command(
        name=locale_str("amidakuji_template_share"),
        description=locale_str("amidakuji_template_share.description"),
    )
    async def command_share_templates(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        db_manager = require_db_manager(interaction)
        user_id = interaction.user.id
        user = db_manager.get_user(user_id, include_shared=False)
        private_templates = user.custom_templates if user else []

        guild_id = interaction.guild_id
        guild_templates: list[Template] = []
        if guild_id is not None:
            guild_templates = db_manager.list_shared_templates(
                scope=TemplateScope.GUILD,
                guild_id=guild_id,
                created_by=user_id,
            )

        public_templates = db_manager.list_shared_templates(
            scope=TemplateScope.PUBLIC,
            created_by=user_id,
        )

        if not private_templates and not guild_templates and not public_templates:
            embed = discord.Embed(
                title="管理できるテンプレートがありません",
                description=(
                    "まずは `/amidakuji_template_create` でテンプレートを作成するか、"
                    "共有設定を追加してください。"
                ),
                color=discord.Color.orange(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        display_name = getattr(interaction.user, "display_name", interaction.user.name)
        view = TemplateSharingView(
            db_manager=db_manager,
            user_id=user_id,
            display_name=display_name,
            guild_id=guild_id,
            private_templates=private_templates,
            guild_templates=guild_templates,
            public_templates=public_templates,
        )

        await interaction.followup.send(
            embed=view.create_embed(),
            view=view,
            ephemeral=True,
        )


__all__ = ["register_commands"]
