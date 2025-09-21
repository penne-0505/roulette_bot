import discord

from models.context_model import CommandContext
from models.model import Template
from models.state_model import AmidakujiState


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


class ApplyOptionsButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="テンプレートを保存")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        choices = list(self.context.options_snapshot)
        template = Template(
            title=self.context.history[AmidakujiState.TEMPLATE_TITLE_ENTERED],
            choices=choices,
        )

        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.TEMPLATE_CREATED,
            template,
            interaction,
        )


class OptionMoveUpButton(discord.ui.Button):
    def __init__(self, context: CommandContext, *, row: int | None = None):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="上へ",
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
            label="下へ",
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


class UseHistoryButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="最後に使ったテンプレート"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MODE_USE_HISTORY,
            interaction,
            interaction,
        )


class UseExistingButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="既存のテンプレート")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MODE_USE_EXISTING,
            interaction,
            interaction,
        )


class UseSharedTemplatesButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="共有テンプレート")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MODE_USE_SHARED,
            interaction,
            interaction,
        )


class UsePublicTemplatesButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="公開テンプレート")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MODE_USE_PUBLIC,
            interaction,
            interaction,
        )


class CreateNewButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.success, label="テンプレートを作成")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MODE_CREATE_NEW,
            interaction,
            interaction,
        )


class DeleteTemplateButton(discord.ui.Button):
    def __init__(self, context: CommandContext, *, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="テンプレートを削除",
            disabled=disabled,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MODE_DELETE_TEMPLATE,
            interaction,
            interaction,
        )


class BackToTemplateSelectButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="テンプレート一覧に戻る"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MODE_USE_EXISTING,
            interaction,
            interaction,
        )


class UseSharedTemplateButton(discord.ui.Button):
    def __init__(self, context: CommandContext, template: Template):
        super().__init__(style=discord.ButtonStyle.primary, label="このテンプレートを使う")
        self.context = context
        self.template = template

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.TEMPLATE_DETERMINED,
            self.template,
            interaction,
        )


class CopySharedTemplateButton(discord.ui.Button):
    def __init__(self, context: CommandContext, template: Template):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="自分用にコピー"
        )
        self.context = context
        self.template = template

    async def callback(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await interaction.response.defer(ephemeral=True)
        await flow.dispatch(
            AmidakujiState.SHARED_TEMPLATE_COPY_REQUESTED,
            self.template,
            interaction,
        )
