import discord

from models.context_model import CommandContext
from models.model import Template
from models.state_model import AmidakujiState
from components.mixins import DisableViewOnCallbackMixin


def _get_flow(context: CommandContext):
    services = context.services
    flow = getattr(services, "flow", None) if services is not None else None
    if flow is None:
        raise RuntimeError("Flow controller is not available")
    return flow


class EnterOptionButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="選択肢を追加する",
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.ENTER_OPTION_BUTTON_CLICKED,
            interaction,
            interaction,
        )


class NeedMoreOptionsButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="さらにオプションを入力"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.NEED_MORE_OPTIONS,
            interaction,
            interaction,
        )


class ApplyOptionsButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="テンプレートを保存")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        choices = list(self.context.options_snapshot)
        template = Template(
            title=str(self.context.history[AmidakujiState.TEMPLATE_TITLE_ENTERED]),
            choices=choices,
        )

        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.TEMPLATE_CREATED,
                template,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)

    def _should_disable_after_dispatch(self) -> bool:
        return self.context.state in {
            AmidakujiState.TEMPLATE_DETERMINED,
            AmidakujiState.TEMPLATE_CREATED,
        }


class OptionMoveUpButton(discord.ui.Button):
    def __init__(self, context: CommandContext, *, row: int | None = None):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="上へ移動",
            row=row,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.OPTION_MOVED_UP,
            interaction,
            interaction,
        )


class OptionMoveDownButton(discord.ui.Button):
    def __init__(self, context: CommandContext, *, row: int | None = None):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="下へ移動",
            row=row,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.OPTION_MOVED_DOWN,
            interaction,
            interaction,
        )


class OptionDeleteButton(discord.ui.Button):
    def __init__(self, context: CommandContext, *, row: int | None = None):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="削除",
            row=row,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.OPTION_DELETED,
            interaction,
            interaction,
        )


class UseHistoryButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="最後に使ったテンプレート"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.MODE_USE_HISTORY,
                interaction,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)


class UseExistingButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="既存のテンプレート")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.MODE_USE_EXISTING,
                interaction,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)


class UseSharedTemplatesButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="サーバー内のテンプレート")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.MODE_USE_SHARED,
                interaction,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)


class UsePublicTemplatesButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="グローバルテンプレート")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.MODE_USE_PUBLIC,
                interaction,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)


class CreateNewButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.success, label="テンプレートを作成")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.MODE_CREATE_NEW,
                interaction,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)


class DeleteTemplateButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext, *, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="テンプレートを削除",
            disabled=disabled,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.MODE_DELETE_TEMPLATE,
                interaction,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)


class BackToTemplateSelectButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="テンプレート一覧に戻る"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.MODE_USE_EXISTING,
                interaction,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)


class UseSharedTemplateButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True

    def __init__(self, context: CommandContext, template: Template):
        super().__init__(style=discord.ButtonStyle.primary, label="このテンプレートを使う")
        self.context = context
        self.template = template

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        try:
            await flow.dispatch(
                AmidakujiState.TEMPLATE_DETERMINED,
                self.template,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)


class CopySharedTemplateButton(DisableViewOnCallbackMixin, discord.ui.Button):
    disable_on_success = True
    disable_entire_view = False

    def __init__(self, context: CommandContext, template: Template):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="自分用にコピー"
        )
        self.context = context
        self.template = template

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await interaction.response.defer(ephemeral=True)
        try:
            await flow.dispatch(
                AmidakujiState.SHARED_TEMPLATE_COPY_REQUESTED,
                self.template,
                interaction,
            )
        except Exception:
            raise
        else:
            await self._cleanup_after_callback(interaction)
