import discord

from data_interface import DataInterface
from db_manager import db
from models.context_model import CommandContext
from models.model import Template
from models.state_model import AmidakujiState


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

        # botを除外
        result = [user for user in result if user is not user.bot]

        self.context.update_context(
            state=AmidakujiState.MEMBER_SELECTED,
            result=result,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()
