from collections.abc import Iterable
from typing import TYPE_CHECKING, TypeVar

import discord

from models.context_model import CommandContext
from models.model import Template
from models.state_model import AmidakujiState

if TYPE_CHECKING:
    from data_interface import DataInterface
    from db_manager import DBManager


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
        from db_manager import db
        from data_interface import DataInterface

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


T = TypeVar("T")


def remove_bots(users: Iterable[T]) -> list[T]:
    """Return users without bot accounts.

    Both ``discord.User`` and ``discord.Member`` expose a ``bot`` attribute, but
    it may be missing for custom implementations in tests.  ``getattr`` with a
    default ensures that we treat objects without the attribute as non-bot
    users.
    """

    return [user for user in users if not getattr(user, "bot", False)]


class MemberSelect(discord.ui.UserSelect):
    def __init__(self, context: CommandContext):
        super().__init__(
            placeholder="あみだくじに参加するメンバーを選択してください",
            min_values=1,
            max_values=25,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        from data_interface import DataInterface

        # Memberの可能性があるので、Userに変換(APIの仕様上、DM内ならUser, サーバー内ならMemberに統一されている)
        result: list[discord.User] = []
        for user in self.values:
            if isinstance(user, discord.User):
                result.append(user)
            elif isinstance(user, discord.Member):
                resolved_user = interaction.client.get_user(user.id)
                if resolved_user is None:
                    try:
                        resolved_user = await interaction.client.fetch_user(user.id)
                    except discord.DiscordException:
                        resolved_user = None
                if resolved_user is not None:
                    result.append(resolved_user)

        # botを除外
        result = remove_bots(result)

        self.context.update_context(
            state=AmidakujiState.MEMBER_SELECTED,
            result=result,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()
