import discord
from data_interface import DataInterface
from model.model import AmidakujiState, CommandContext


class MemberSelect(discord.ui.UserSelect):
    def __init__(self, context: CommandContext):
        super().__init__(
            placeholder="あみだくじに参加するメンバーを選択してください",
            min_values=1,
            max_values=25,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        interface = DataInterface(
            CommandContext(
                interaction=interaction,
                state=AmidakujiState.MEMBER_SELECTED,
                result=interaction.data.get("values"),
                history=self.context.history,
            )
        )
        interface.forward()


class UseExisting(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="テンプレートを使う"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        interface = DataInterface(
            CommandContext(
                interaction=interaction,
                state=AmidakujiState.MODE_USE_EXISTING,
                result="existing",
                history=self.context.history,
            )
        )
        interface.forward()


class CreateNew(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="テンプレートを作成"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        interface = DataInterface(
            CommandContext(
                interaction=interaction,
                state=AmidakujiState.MODE_CREATE_NEW,
                result="new",
                history=self.context.history,
            )
        )
        interface.forward()


class UseHistory(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="直近のテンプレートを使う"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        interface = DataInterface(
            CommandContext(
                interaction=interaction,
                state=AmidakujiState.MODE_USE_HISTORY,
                result="history",
                history=self.context.history,
            )
        )
        interface.forward()


class SelectTemplate(discord.ui.Select):
    def __init__(self, context: CommandContext, templates: list[str]):
        super().__init__(
            placeholder="テンプレートを選択してください",
            options=[
                discord.SelectOption(label=template, value=template)
                for template in templates
            ],
        )
        self.context = context


class MemberSelectView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(MemberSelect(context))
