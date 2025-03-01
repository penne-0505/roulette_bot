import discord

from data_interface import DataInterface
from db_manager import db
from model.context_model import CommandContext
from model.model import Template
from model.state_model import AmidakujiState


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
        super().__init__(style=discord.ButtonStyle.premium, label="テンプレートを作成")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.MODE_CREATE_NEW,
            result=interaction,
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


class TemplateSelect(discord.ui.Select):
    def __init__(self, context: CommandContext, templates: list[Template]):
        # templatesからSelectOptionを作成
        super().__init__(
            placeholder="テンプレートを選択してください",
            options=[
                discord.SelectOption(label=template.title) for template in templates
            ],
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        # 取得した値を元にテンプレートを取得
        selected_template_title = self.values[0]
        current_user = db.get_user(interaction.user.id)
        user_templates = current_user.custom_templates
        selected_template = next(
            t for t in user_templates if t.title == selected_template_title
        )

        self.context.update_context(
            state=AmidakujiState.TEMPLATE_DETERMINED,
            result=selected_template,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class MemberSelect(discord.ui.UserSelect):
    def __init__(self, context: CommandContext):
        super().__init__(
            placeholder="あみだくじに参加するメンバーを選択してください",
            min_values=1,
            max_values=25,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        # Memberの可能性があるので、Userに変換(APIの仕様上、DM内ならUser, サーバー内ならMemberに統一されている)
        result = []
        for user in self.values:
            if isinstance(user, discord.User):
                result.append(user)
            elif isinstance(user, discord.Member):
                result.append(self.context.interaction.client.get_user(user.id))

        self.context.update_context(
            state=AmidakujiState.MEMBER_SELECTED,
            result=result,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class MemberSelectView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(MemberSelect(context))


class SelectTemplateView(discord.ui.View):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(timeout=300)
        self.add_item(TemplateSelect(context, templates))


class ModeSelectionView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(UseExistingButton(context))
        self.add_item(UseHistoryButton(context))
        # 新規作成は将来的に実装する(modalをループして表示するときの状態管理がめんどくさい)
        # self.add_item(CreateNewButton(context))
