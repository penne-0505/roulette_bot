import discord

from data_interface import DataInterface
from models.context_model import CommandContext
from models.model import Template
from models.state_model import AmidakujiState


class EnterOptionButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="次のステップ")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.ENTER_OPTION_BUTTON_CLICKED,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class NeedMoreOptionsButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="さらにオプションを入力"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.NEED_MORE_OPTIONS,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class ApplyOptionsButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="テンプレートを保存")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        template = Template(
            title=self.context.history[AmidakujiState.TEMPLATE_TITLE_ENTERED],
            choices=self.context.history[AmidakujiState.OPTION_NAME_ENTERED],
        )

        self.context.update_context(
            state=AmidakujiState.TEMPLATE_CREATED,
            result=template,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class UseHistoryButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="最後に使ったテンプレート"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.MODE_USE_HISTORY,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class UseExistingButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="既存のテンプレート")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.MODE_USE_EXISTING,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class CreateNewButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.success, label="テンプレートを作成")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.MODE_CREATE_NEW,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()
