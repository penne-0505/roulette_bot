import discord
from data_interface import DataInterface
from model.context_model import CommandContext
from model.model import Template
from model.state_model import AmidakujiState


class MemberSelect(discord.ui.UserSelect):
    def __init__(self, context: CommandContext):
        super().__init__(
            placeholder="あみだくじに参加するメンバーを選択してください",
            min_values=1,
            max_values=25,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        # Memberの可能性があるので、Userに変換
        result = []
        for user in self.values:
            if isinstance(user, discord.User):
                result.append(user)
            elif isinstance(user, discord.Member):
                result.append(self.context.interaction.client.get_user(user.id))

        context = CommandContext(
            interaction=interaction,
            state=AmidakujiState.MEMBER_SELECTED,
            result=result,
        )

        self.context.add_to_history(state=AmidakujiState.MEMBER_SELECTED, result=result)

        interface = DataInterface(context=context)
        await interface.forward()


class UseExistingButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="テンプレートを使う"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        context = CommandContext(
            interaction=interaction,
            state=AmidakujiState.MODE_USE_EXISTING,
            result="existing",
        )

        context.add_to_history(
            state=AmidakujiState.MODE_USE_EXISTING, result=interaction
        )

        interface = DataInterface(context=context)
        await interface.forward()


class CreateNewButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="テンプレートを作成"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        context = CommandContext(
            interaction=interaction,
            state=AmidakujiState.MODE_CREATE_NEW,
            result="new",
        )

        context.add_to_history(state=AmidakujiState.MODE_CREATE_NEW, result=interaction)

        interface = DataInterface(context=context)
        await interface.forward()


class UseHistoryButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="直近のテンプレートを使う"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        context = CommandContext(
            interaction=interaction,
            state=AmidakujiState.MODE_USE_HISTORY,
            result="history",
        )

        context.add_to_history(
            state=AmidakujiState.MODE_USE_HISTORY, result=interaction
        )

        interface = DataInterface(context=context)
        await interface.forward()


class SelectTemplate(discord.ui.Select):
    def __init__(self, context: CommandContext, templates: list[Template]):
        # templatesからSelectOptionを作成
        super().__init__(
            placeholder="テンプレートを選択してください",
            options=[
                discord.SelectOption(label=template.title, value=template.id)
                for template in templates
            ],
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        selected_template = self.values[0]

        context = CommandContext(
            interaction=interaction,
            state=AmidakujiState.TEMPLATE_DETERMINED,
            result=selected_template,
        )

        context.add_to_history(
            state=AmidakujiState.TEMPLATE_DETERMINED, result=selected_template
        )

        interface = DataInterface(context=context)
        interface.forward()


class MemberSelectView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(MemberSelect(context))


class SelectTemplateView(discord.ui.View):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(timeout=300)
        self.add_item(SelectTemplate(context, templates))


class ModeSelectionView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(UseExistingButton(context))
        self.add_item(UseHistoryButton(context))
        # 新規作成は将来的に実装する(modalをループして表示するときの状態管理がめんどくさい)
        # self.add_item(CreateNewButton(context))
