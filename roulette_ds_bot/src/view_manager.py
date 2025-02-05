import discord
from data_interface import DataInterface
from utils import AmidakujiState, CommandContext


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
        interface.foward()


class ModeSelect(discord.ui.Select):
    def __init__(self, context: CommandContext):
        # fmt: off
        super().__init__(
            placeholder="あみだくじの種類を選択してください",
            options=[
                discord.SelectOption(label='既存のテンプレートから選ぶ', value='existing'),
                discord.SelectOption(label='テンプレートを新規作成する', value='new'),
                discord.SelectOption(label='最後に選択したテンプレートを使う', value='history'),
            ],
        )
        # fmt: on
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        interface = DataInterface(
            CommandContext(
                interaction=interaction,
                state=AmidakujiState.MODE_SELECTED,
                result=interaction.data.get("values"),
                history=self.context.history,
            )
        )
        interface.foward()


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


class ModeSelectView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(ModeSelect(context))
