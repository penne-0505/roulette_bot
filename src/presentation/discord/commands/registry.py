"""Slash コマンドの登録処理。"""
from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING

import discord
import psutil
from discord.app_commands import locale_str

from application.dto import SharedTemplateSetDTO
from data_interface import FlowController
from domain import ResultEmbedMode, SelectionMode, TemplateScope
from models.context_model import CommandContext
from models.state_model import AmidakujiState
from presentation.discord.client import BotClient
from presentation.discord.components.embeds import (
    create_embed_mode_overview_embed,
    create_selection_mode_overview_embed,
)
from presentation.discord.services import CommandRuntimeServices
from presentation.discord.views.embed_mode import EmbedModeView
from presentation.discord.views.history_list import HistoryListView
from presentation.discord.views.selection_mode import SelectionModeView
from presentation.discord.views.state import (
    EmbedModeState,
    SelectionModeState,
    TemplateListViewState,
    TemplateManagementState,
    TemplateSharingState,
)
from presentation.discord.views.template_list import TemplateListView
from presentation.discord.views.template_management import TemplateManagementView
from presentation.discord.views.template_sharing import TemplateSharingView
from presentation.discord.views.view import ModeSelectionView

if TYPE_CHECKING:  # pragma: no cover - 型チェック専用
    from presentation.discord.client import BotClient as BotClientProtocol


def _resolve_client(interaction: discord.Interaction) -> BotClient:
    client = interaction.client
    if not isinstance(client, BotClient):
        raise RuntimeError("Discord BotClient 以外のクライアントでは利用できません。")
    return client


def _build_runtime_services(
    interaction: discord.Interaction,
) -> CommandRuntimeServices:
    client = _resolve_client(interaction)
    return CommandRuntimeServices.from_client(
        repository=client.db,
        usecases=client.command_usecases,
    )


def register_commands(client: "BotClientProtocol") -> None:
    """BotClient にスラッシュコマンドを紐付ける。"""

    tree = client.tree

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
        except Exception:  # pragma: no cover - Discord API の例外は環境依存
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

        services = _build_runtime_services(interaction)
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
        services = _build_runtime_services(interaction)
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

        services = _build_runtime_services(interaction)
        template_service = services.template_service
        user_id = interaction.user.id
        guild_id = interaction.guild_id

        private_templates = template_service.list_private_templates(
            user_id=user_id,
            guild_id=guild_id,
        ).templates

        if not private_templates:
            embed = discord.Embed(
                title="テンプレートはまだありません",
                description="まずは `/amidakuji_template_create` でテンプレートを作成してください。",
                color=discord.Color.orange(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        state = TemplateManagementState(user_id=user_id, templates=private_templates)
        view = TemplateManagementView(state=state, template_service=template_service)

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

        services = _build_runtime_services(interaction)
        history_service = services.history_service

        raw_mode = history_service.get_embed_mode()
        try:
            current_mode = ResultEmbedMode(str(raw_mode))
        except ValueError:  # pragma: no cover - 不正値は初期値へフォールバック
            current_mode = ResultEmbedMode.COMPACT

        state = EmbedModeState(current_mode=current_mode, user_id=interaction.user.id)
        embed = create_embed_mode_overview_embed(current_mode)
        view = EmbedModeView(state=state, history_service=history_service)

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

        services = _build_runtime_services(interaction)
        template_service = services.template_service
        user_id = interaction.user.id
        guild_id = interaction.guild_id

        private_dto, guild_dto, public_dto = template_service.get_template_overview(
            user_id=user_id,
            guild_id=guild_id,
        )
        state = TemplateListViewState.from_dtos(
            private=private_dto,
            guild=guild_dto,
            public=public_dto,
        )
        view = TemplateListView(state=state)

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

        services = _build_runtime_services(interaction)
        history_service = services.history_service

        current_mode = history_service.get_selection_mode()

        state = SelectionModeState(
            current_mode=current_mode,
            user_id=interaction.user.id,
        )
        embed = create_selection_mode_overview_embed(current_mode)
        view = SelectionModeView(state=state, history_service=history_service)

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

        services = _build_runtime_services(interaction)

        view = HistoryListView(
            history_service=services.history_service,
            guild_id=interaction.guild_id or 0,
            page_size=5,
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

        services = _build_runtime_services(interaction)
        template_service = services.template_service
        user_id = interaction.user.id
        guild_id = interaction.guild_id

        private_templates = template_service.list_private_templates(
            user_id=user_id,
            guild_id=guild_id,
        )
        guild_templates = template_service.list_shared_templates_by_scope(
            scope=TemplateScope.GUILD,
            guild_id=guild_id,
            created_by=user_id,
        )
        public_templates = template_service.list_shared_templates_by_scope(
            scope=TemplateScope.PUBLIC,
            created_by=user_id,
        )

        if (
            not private_templates.templates
            and not guild_templates.templates
            and not public_templates.templates
        ):
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
        shared_set = SharedTemplateSetDTO(
            shared_templates=list(guild_templates.templates),
            public_templates=list(public_templates.templates),
        )
        state = TemplateSharingState.from_dtos(
            user_id=user_id,
            display_name=display_name,
            guild_id=guild_id,
            private=private_templates,
            shared=shared_set,
        )

        view = TemplateSharingView(state=state, template_service=template_service)

        await interaction.followup.send(
            embed=view.create_embed(),
            view=view,
            ephemeral=True,
        )


__all__ = ["register_commands"]
