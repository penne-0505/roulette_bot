from __future__ import annotations

from enum import Enum, auto
from typing import Dict, Iterable, List, Optional

import discord

from db_manager import DBManager
from models.model import Template, TemplateScope
from utils import generate_template_id


class ShareAction(Enum):
    SHARE_GUILD = auto()
    SHARE_PUBLIC = auto()
    UNSHARE_GUILD = auto()
    UNSHARE_PUBLIC = auto()


class TemplateSharingView(discord.ui.View):
    """View for sharing or unsharing templates."""

    def __init__(
        self,
        *,
        db_manager: DBManager,
        user_id: int,
        display_name: str,
        guild_id: Optional[int],
        private_templates: Iterable[Template],
        guild_templates: Iterable[Template],
        public_templates: Iterable[Template],
    ) -> None:
        super().__init__(timeout=300)
        self.db_manager = db_manager
        self.user_id = user_id
        self.display_name = display_name
        self.guild_id = guild_id
        self.private_templates: Dict[str, Template] = {
            template.template_id: template for template in private_templates
        }
        self.guild_templates: Dict[str, Template] = {
            template.template_id: template for template in guild_templates
        }
        self.public_templates: Dict[str, Template] = {
            template.template_id: template for template in public_templates
        }
        self.current_action: Optional[ShareAction] = None

        self.share_guild_button = _ShareToGuildButton(self)
        self.share_public_button = _ShareToPublicButton(self)
        self.unshare_guild_button = _UnshareGuildButton(self)
        self.unshare_public_button = _UnsharePublicButton(self)
        self.template_select = _SharingTemplateSelect(self)
        self.close_button = _CloseButton(self)

        self.add_item(self.share_guild_button)
        self.add_item(self.share_public_button)
        self.add_item(self.unshare_guild_button)
        self.add_item(self.unshare_public_button)
        self.add_item(self.template_select)
        self.add_item(self.close_button)

        self._update_components()

    def _update_components(self) -> None:
        has_private = bool(self.private_templates)
        has_guild_shared = bool(self.guild_templates)
        has_public_shared = bool(self.public_templates)
        self.share_guild_button.disabled = self.guild_id is None or not has_private
        self.share_public_button.disabled = not has_private
        self.unshare_guild_button.disabled = not has_guild_shared
        self.unshare_public_button.disabled = not has_public_shared
        self.template_select.update_options()

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title="テンプレート共有・公開", color=discord.Color.blurple())
        if self.current_action is None:
            embed.description = "操作を選択してください。"
            return embed

        if self.current_action is ShareAction.SHARE_GUILD:
            if self.guild_id is None:
                embed.description = "サーバー内でのみ共有できます。"
            else:
                embed.description = "共有するテンプレートを選択してください。"
        elif self.current_action is ShareAction.SHARE_PUBLIC:
            embed.description = "公開するテンプレートを選択してください。"
        elif self.current_action is ShareAction.UNSHARE_GUILD:
            embed.description = "共有解除するテンプレートを選択してください。"
        else:
            embed.description = "公開解除するテンプレートを選択してください。"

        embed.add_field(
            name="プライベート",
            value=str(len(self.private_templates)),
            inline=True,
        )
        embed.add_field(
            name="共有中",
            value=str(len(self.guild_templates)),
            inline=True,
        )
        embed.add_field(
            name="公開中",
            value=str(len(self.public_templates)),
            inline=True,
        )
        return embed

    async def render(
        self,
        interaction: discord.Interaction,
        *,
        status_message: Optional[str] = None,
    ) -> None:
        self._update_components()
        embed = self.create_embed()
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)
        if status_message:
            await interaction.followup.send(status_message, ephemeral=True)

    def set_action(self, action: ShareAction) -> None:
        self.current_action = action
        self.template_select.update_options()

    async def handle_selection(self, interaction: discord.Interaction, template_id: str) -> None:
        if self.current_action is None:
            await interaction.response.defer(thinking=False)
            return

        if self.current_action is ShareAction.SHARE_GUILD:
            message = await self._share_to_guild(template_id)
        elif self.current_action is ShareAction.SHARE_PUBLIC:
            message = await self._share_to_public(template_id)
        elif self.current_action is ShareAction.UNSHARE_GUILD:
            message = await self._unshare_guild(template_id)
        else:
            message = await self._unshare_public(template_id)

        await self.render(interaction, status_message=message)

    async def _share_to_guild(self, template_id: str) -> str:
        if self.guild_id is None:
            return "サーバー内でのみ共有できます。"
        template = self.private_templates.get(template_id)
        if template is None:
            return "テンプレートが見つかりません。"

        existing = self.db_manager.list_shared_templates(
            scope=TemplateScope.GUILD,
            guild_id=self.guild_id,
        )
        existing_titles = {item.title for item in existing}
        new_title, renamed = self._resolve_title(template.title, existing_titles)
        shared_template = Template(
            title=new_title,
            choices=list(template.choices),
            scope=TemplateScope.GUILD,
            created_by=self.user_id,
            guild_id=self.guild_id,
            template_id=generate_template_id(),
        )
        shared_template = self.db_manager.create_shared_template(shared_template)
        self.guild_templates[shared_template.template_id] = shared_template
        if renamed:
            return f"テンプレートを共有しました（名称を「{new_title}」に変更しました）。"
        return "テンプレートを共有しました。"

    async def _share_to_public(self, template_id: str) -> str:
        template = self.private_templates.get(template_id)
        if template is None:
            return "テンプレートが見つかりません。"

        existing = self.db_manager.list_shared_templates(scope=TemplateScope.PUBLIC)
        existing_titles = {item.title for item in existing}
        new_title, renamed = self._resolve_title(template.title, existing_titles)
        shared_template = Template(
            title=new_title,
            choices=list(template.choices),
            scope=TemplateScope.PUBLIC,
            created_by=self.user_id,
            guild_id=None,
            template_id=generate_template_id(),
        )
        shared_template = self.db_manager.create_shared_template(shared_template)
        self.public_templates[shared_template.template_id] = shared_template
        if renamed:
            return f"テンプレートを公開しました（名称を「{new_title}」に変更しました）。"
        return "テンプレートを公開しました。"

    async def _unshare_guild(self, template_id: str) -> str:
        template = self.guild_templates.get(template_id)
        if template is None:
            return "共有テンプレートが見つかりません。"

        self.db_manager.delete_shared_template(template_id)
        del self.guild_templates[template_id]
        return "共有を解除しました。"

    async def _unshare_public(self, template_id: str) -> str:
        template = self.public_templates.get(template_id)
        if template is None:
            return "公開テンプレートが見つかりません。"

        self.db_manager.delete_shared_template(template_id)
        del self.public_templates[template_id]
        return "公開を解除しました。"

    def _resolve_title(self, base_title: str, existing_titles: set[str]) -> tuple[str, bool]:
        if base_title not in existing_titles:
            return base_title, False

        candidate = f"{base_title} ({self.display_name})"
        if candidate not in existing_titles:
            return candidate, True

        counter = 2
        while True:
            candidate = f"{base_title} ({self.display_name} {counter})"
            if candidate not in existing_titles:
                return candidate, True
            counter += 1


class _SharingTemplateSelect(discord.ui.Select):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(placeholder="テンプレートを選択してください", min_values=1, max_values=1)
        self.view = view
        self.disabled = True

    def update_options(self) -> None:
        action = self.view.current_action
        options: List[discord.SelectOption] = []
        if action is ShareAction.SHARE_GUILD:
            source = self.view.private_templates
        elif action is ShareAction.SHARE_PUBLIC:
            source = self.view.private_templates
        elif action is ShareAction.UNSHARE_GUILD:
            source = self.view.guild_templates
        elif action is ShareAction.UNSHARE_PUBLIC:
            source = self.view.public_templates
        else:
            source = {}

        if not source:
            self.options = []
            self.disabled = True
            return

        for template in source.values():
            description = " / ".join(template.choices[:3]) if template.choices else "(候補なし)"
            options.append(
                discord.SelectOption(
                    label=template.title,
                    value=template.template_id,
                    description=description[:100] if description else None,
                )
            )
        self.options = options
        self.disabled = False

    async def callback(self, interaction: discord.Interaction) -> None:
        template_id = self.values[0]
        await self.view.handle_selection(interaction, template_id)


class _ShareToGuildButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="サーバーで共有")
        self.view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.set_action(ShareAction.SHARE_GUILD)
        await self.view.render(interaction)


class _ShareToPublicButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="グローバル公開")
        self.view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.set_action(ShareAction.SHARE_PUBLIC)
        await self.view.render(interaction)


class _UnshareGuildButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="共有を解除")
        self.view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.set_action(ShareAction.UNSHARE_GUILD)
        await self.view.render(interaction)


class _UnsharePublicButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="公開を解除")
        self.view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.set_action(ShareAction.UNSHARE_PUBLIC)
        await self.view.render(interaction)


class _CloseButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="閉じる")
        self.view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        for child in self.view.children:
            child.disabled = True
        await self.view.render(interaction, status_message="テンプレート共有を終了しました。")
        self.view.stop()
