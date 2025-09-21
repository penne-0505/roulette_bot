from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import discord

from db_manager import DBManager
from models.model import Template, TemplateScope
from utils import generate_template_id


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
        self.selected_scope: Optional[TemplateScope] = None
        self.selected_template_id: Optional[str] = None

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
        self._ensure_selection_valid()
        self.template_select.update_options()

        scope = self.selected_scope
        self.share_guild_button.disabled = (
            self.guild_id is None or scope is not TemplateScope.PRIVATE
        )
        self.share_public_button.disabled = scope is not TemplateScope.PRIVATE
        self.unshare_guild_button.disabled = scope is not TemplateScope.GUILD
        self.unshare_public_button.disabled = scope is not TemplateScope.PUBLIC

    def _ensure_selection_valid(self) -> None:
        if self.selected_scope is None or self.selected_template_id is None:
            return

        templates_by_scope = {
            TemplateScope.PRIVATE: self.private_templates,
            TemplateScope.GUILD: self.guild_templates,
            TemplateScope.PUBLIC: self.public_templates,
        }
        templates = templates_by_scope.get(self.selected_scope)
        if not templates or self.selected_template_id not in templates:
            self.selected_scope = None
            self.selected_template_id = None

    @staticmethod
    def _create_status_embed(message: str) -> discord.Embed:
        """補助メッセージ表示用の簡易 Embed を生成する。"""

        return discord.Embed(description=message, color=discord.Color.blurple())

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title="テンプレート共有・公開", color=discord.Color.blurple())
        template: Optional[Template] = None
        if self.selected_scope is not None and self.selected_template_id is not None:
            template = self._get_template(self.selected_scope, self.selected_template_id)

        if template is None:
            embed.description = "共有・公開するテンプレートを選択してください。"
        elif self.selected_scope is TemplateScope.PRIVATE:
            embed.description = f"テンプレート「{template.title}」の共有先を選んでください。"
        elif self.selected_scope is TemplateScope.GUILD:
            embed.description = f"テンプレート「{template.title}」はサーバーで共有中です。共有を解除できます。"
        else:
            embed.description = f"テンプレート「{template.title}」は公開中です。公開を解除できます。"

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

    def _get_template(
        self, scope: TemplateScope, template_id: str
    ) -> Optional[Template]:
        if scope is TemplateScope.PRIVATE:
            return self.private_templates.get(template_id)
        if scope is TemplateScope.GUILD:
            return self.guild_templates.get(template_id)
        if scope is TemplateScope.PUBLIC:
            return self.public_templates.get(template_id)
        return None

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
            await interaction.followup.send(
                embed=self._create_status_embed(status_message),
                ephemeral=True,
            )

    async def handle_selection(
        self,
        interaction: discord.Interaction,
        scope: TemplateScope,
        template_id: str,
    ) -> None:
        template = self._get_template(scope, template_id)
        if template is None:
            await self.render(interaction, status_message="テンプレートが見つかりません。")
            return

        self.selected_scope = scope
        self.selected_template_id = template_id
        await self.render(interaction)

    async def share_to_guild(self, interaction: discord.Interaction) -> None:
        if self.selected_scope is not TemplateScope.PRIVATE or self.selected_template_id is None:
            await self.render(interaction, status_message="共有するテンプレートを選択してください。")
            return

        message = await self._share_to_guild(self.selected_template_id)
        await self.render(interaction, status_message=message)

    async def share_to_public(self, interaction: discord.Interaction) -> None:
        if self.selected_scope is not TemplateScope.PRIVATE or self.selected_template_id is None:
            await self.render(interaction, status_message="共有するテンプレートを選択してください。")
            return

        message = await self._share_to_public(self.selected_template_id)
        await self.render(interaction, status_message=message)

    async def unshare_guild(self, interaction: discord.Interaction) -> None:
        if self.selected_scope is not TemplateScope.GUILD or self.selected_template_id is None:
            await self.render(interaction, status_message="共有解除するテンプレートを選択してください。")
            return

        template_id = self.selected_template_id
        message = await self._unshare_guild(template_id)
        self.selected_scope = None
        self.selected_template_id = None
        await self.render(interaction, status_message=message)

    async def unshare_public(self, interaction: discord.Interaction) -> None:
        if self.selected_scope is not TemplateScope.PUBLIC or self.selected_template_id is None:
            await self.render(interaction, status_message="公開解除するテンプレートを選択してください。")
            return

        template_id = self.selected_template_id
        message = await self._unshare_public(template_id)
        self.selected_scope = None
        self.selected_template_id = None
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
        self.template_view = view
        self.disabled = True

    def update_options(self) -> None:
        view = self.template_view
        options: List[discord.SelectOption] = []

        def append_options(
            source: Dict[str, Template],
            scope: TemplateScope,
            category_label: str,
        ) -> None:
            for template in source.values():
                choice_preview = " / ".join(template.choices[:3]) if template.choices else "(候補なし)"
                description_parts = [category_label]
                if choice_preview:
                    description_parts.append(choice_preview)
                description = " / ".join(description_parts)
                options.append(
                    discord.SelectOption(
                        label=template.title,
                        value=f"{scope.value}:{template.template_id}",
                        description=description[:100],
                        default=(
                            view.selected_scope is scope
                            and view.selected_template_id == template.template_id
                        ),
                    )
                )

        append_options(view.private_templates, TemplateScope.PRIVATE, "プライベート")
        append_options(view.guild_templates, TemplateScope.GUILD, "サーバー共有")
        append_options(view.public_templates, TemplateScope.PUBLIC, "公開")

        if options:
            self.options = options
            self.disabled = False
        else:
            self.options = [
                discord.SelectOption(
                    label="選択可能なテンプレートがありません",
                    value="_DISABLED_",
                )
            ]
            self.disabled = True

    async def callback(self, interaction: discord.Interaction) -> None:
        value = self.values[0]
        if value == "_DISABLED_":
            await interaction.response.defer(thinking=False)
            return

        scope_value, template_id = value.split(":", 1)
        scope = TemplateScope(scope_value)
        await self.template_view.handle_selection(interaction, scope, template_id)


class _ShareToGuildButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="サーバーで共有")
        self.template_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.template_view.share_to_guild(interaction)


class _ShareToPublicButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="グローバル公開")
        self.template_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.template_view.share_to_public(interaction)


class _UnshareGuildButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="共有を解除")
        self.template_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.template_view.unshare_guild(interaction)


class _UnsharePublicButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="公開を解除")
        self.template_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.template_view.unshare_public(interaction)


class _CloseButton(discord.ui.Button):
    def __init__(self, view: TemplateSharingView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="閉じる")
        self.template_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        for child in self.template_view.children:
            child.disabled = True
        await self.template_view.render(interaction, status_message="テンプレート共有を終了しました。")
        self.template_view.stop()
