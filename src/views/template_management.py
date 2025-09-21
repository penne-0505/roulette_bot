from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import discord

from db_manager import DBManager
from models.model import Template, TemplateScope


@dataclass
class TemplateEditSession:
    template_id: str
    original_title: str
    original_choices: List[str]
    title: str
    choices: List[str]
    selected_index: Optional[int] = None

    @classmethod
    def from_template(cls, template: Template) -> "TemplateEditSession":
        return cls(
            template_id=template.template_id,
            original_title=template.title,
            original_choices=list(template.choices),
            title=template.title,
            choices=list(template.choices),
        )

    @property
    def changed(self) -> bool:
        return self.title != self.original_title or self.choices != self.original_choices

    def reset_with(self, template: Template) -> None:
        self.template_id = template.template_id
        self.original_title = template.title
        self.original_choices = list(template.choices)
        self.title = template.title
        self.choices = list(template.choices)
        self.selected_index = None

    def ensure_selected(self) -> None:
        if self.choices and self.selected_index is None:
            self.selected_index = 0

    def set_selected(self, index: Optional[int]) -> None:
        self.selected_index = index

    def add_choice(self, choice: str) -> None:
        self.choices.append(choice)
        self.selected_index = len(self.choices) - 1

    def rename_choice(self, choice: str) -> None:
        if self.selected_index is None:
            raise ValueError("No option selected")
        self.choices[self.selected_index] = choice

    def delete_selected(self) -> str:
        if self.selected_index is None:
            raise ValueError("No option selected")
        removed = self.choices.pop(self.selected_index)
        if not self.choices:
            self.selected_index = None
        else:
            self.selected_index = min(self.selected_index, len(self.choices) - 1)
        return removed

    def to_template(self, user_id: int) -> Template:
        return Template(
            title=self.title,
            choices=list(self.choices),
            scope=TemplateScope.PRIVATE,
            created_by=user_id,
            guild_id=None,
            template_id=self.template_id,
        )


class TemplateManagementView(discord.ui.View):
    """View that allows users to edit or delete their templates interactively."""

    def __init__(
        self,
        *,
        db_manager: DBManager,
        user_id: int,
        templates: Iterable[Template],
    ) -> None:
        super().__init__(timeout=300)
        self.db_manager = db_manager
        self.user_id = user_id
        self.templates: Dict[str, Template] = {template.template_id: template for template in templates}
        self.session: Optional[TemplateEditSession] = None

        self.template_select = _TemplateSelect(self)
        self.option_select = _TemplateOptionSelect(self)
        self.rename_title_button = _RenameTitleButton(self)
        self.add_option_button = _AddOptionButton(self)
        self.rename_option_button = _RenameOptionButton(self)
        self.delete_option_button = _DeleteOptionButton(self)
        self.save_button = _SaveButton(self)
        self.discard_button = _DiscardButton(self)
        self.delete_template_button = _DeleteTemplateButton(self)
        self.close_button = _CloseButton(self)

        self.add_item(self.template_select)
        self.add_item(self.option_select)
        self.add_item(self.rename_title_button)
        self.add_item(self.add_option_button)
        self.add_item(self.rename_option_button)
        self.add_item(self.delete_option_button)
        self.add_item(self.save_button)
        self.add_item(self.discard_button)
        self.add_item(self.delete_template_button)
        self.add_item(self.close_button)

        self._refresh_template_options()
        self._update_component_states()

    def _refresh_template_options(self) -> None:
        options: List[discord.SelectOption] = []
        for template in self.templates.values():
            label = template.title
            description = " / ".join(template.choices[:3]) if template.choices else "(候補なし)"
            options.append(
                discord.SelectOption(
                    label=label,
                    value=template.template_id,
                    description=description[:100] if description else None,
                )
            )
        self.template_select.refresh(options)

    def _update_component_states(self) -> None:
        has_template = self.session is not None
        has_options = bool(self.session and self.session.choices)
        self.template_select.disabled = not self.templates
        self.option_select.set_session(self.session)
        self.rename_title_button.disabled = not has_template
        self.add_option_button.disabled = not has_template
        self.rename_option_button.disabled = not has_options
        self.delete_option_button.disabled = not has_options
        self.save_button.disabled = not (has_template and self.session and self.session.changed)
        self.discard_button.disabled = not (has_template and self.session and self.session.changed)
        self.delete_template_button.disabled = not has_template

    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="テンプレート管理", color=discord.Color.blurple())
        if not self.templates:
            embed.description = "管理対象のテンプレートが見つかりません。"
            return embed

        if self.session is None:
            embed.description = "テンプレートを選択して編集または削除を行ってください。"
            return embed

        selected_index = self.session.selected_index
        choices_text = "\n".join(
            f"{index + 1}. {'**' if selected_index is not None and index == selected_index else ''}{choice}{'**' if selected_index is not None and index == selected_index else ''}"
            for index, choice in enumerate(self.session.choices)
        )
        if not choices_text:
            choices_text = "(候補なし)"

        status = "変更あり" if self.session.changed else "変更なし"

        embed.add_field(name="タイトル", value=self.session.title, inline=False)
        embed.add_field(name="候補", value=choices_text, inline=False)
        embed.set_footer(text=status)
        return embed

    def create_embed(self) -> discord.Embed:
        return self._build_embed()

    async def render(
        self,
        interaction: discord.Interaction,
        *,
        status_message: Optional[str] = None,
    ) -> None:
        self._refresh_template_options()
        self._update_component_states()
        embed = self._build_embed()
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)
        if status_message:
            await interaction.followup.send(status_message, ephemeral=True)

    def select_template(self, template_id: str) -> str | None:
        template = self.templates.get(template_id)
        if template is None:
            return "選択したテンプレートが見つかりません。"

        notice: Optional[str] = None
        if self.session and self.session.changed:
            notice = "選択を変更したため、未保存の変更を破棄しました。"

        if self.session is None:
            self.session = TemplateEditSession.from_template(template)
        else:
            self.session.reset_with(template)

        return notice

    async def save_changes(self, interaction: discord.Interaction) -> str:
        if self.session is None:
            return "テンプレートが選択されていません。"

        template = self.session.to_template(self.user_id)
        self.db_manager.update_custom_template(self.user_id, template)
        self.templates[template.template_id] = template
        self.session.reset_with(template)
        return "テンプレートを保存しました。"

    async def delete_current_template(self, interaction: discord.Interaction) -> str:
        if self.session is None:
            return "テンプレートが選択されていません。"

        template_id = self.session.template_id
        template = self.templates.get(template_id)
        if template is None:
            return "テンプレートが見つかりません。"

        self.db_manager.delete_custom_template(self.user_id, template_id=template_id)
        del self.templates[template_id]
        self.session = None
        return f"テンプレート「{template.title}」を削除しました。"


class _TemplateSelect(discord.ui.Select):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(placeholder="テンプレートを選択してください", min_values=1, max_values=1)

    def refresh(self, options: List[discord.SelectOption]) -> None:
        self.options = options

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.view.templates:
            await interaction.response.defer(thinking=False)
            return

        template_id = self.values[0]
        notice = self.view.select_template(template_id)
        await self.view.render(interaction, status_message=notice)


class _TemplateOptionSelect(discord.ui.Select):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(
            placeholder="編集する候補を選択してください",
            min_values=1,
            max_values=1,
        )
        self.disabled = True

    def set_session(self, session: Optional[TemplateEditSession]) -> None:
        if session is None or not session.choices:
            self.options = []
            self.disabled = True
            return

        options: List[discord.SelectOption] = []
        selected_index = session.selected_index
        for index, choice in enumerate(session.choices):
            options.append(
                discord.SelectOption(
                    label=f"{index + 1}. {choice}",
                    value=str(index),
                    default=(selected_index is not None and index == selected_index),
                )
            )
        self.options = options
        self.disabled = False

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.view.session is None:
            await interaction.response.defer(thinking=False)
            return

        try:
            index = int(self.values[0])
        except ValueError:
            await interaction.response.defer(thinking=False)
            return

        self.view.session.set_selected(index)
        await self.view.render(interaction)


class _RenameTitleButton(discord.ui.Button):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="タイトルを変更")

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.view.session is None:
            await interaction.response.send_message("テンプレートを選択してください。", ephemeral=True)
            return

        modal = _RenameTitleModal(self.view)
        await interaction.response.send_modal(modal)


class _AddOptionButton(discord.ui.Button):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="候補を追加")

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.view.session is None:
            await interaction.response.send_message("テンプレートを選択してください。", ephemeral=True)
            return

        modal = _AddOptionModal(self.view)
        await interaction.response.send_modal(modal)


class _RenameOptionButton(discord.ui.Button):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="候補をリネーム")

    async def callback(self, interaction: discord.Interaction) -> None:
        session = self.view.session
        if session is None or session.selected_index is None:
            await interaction.response.send_message("候補を選択してください。", ephemeral=True)
            return

        modal = _RenameOptionModal(self.view)
        await interaction.response.send_modal(modal)


class _DeleteOptionButton(discord.ui.Button):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(style=discord.ButtonStyle.danger, label="候補を削除")

    async def callback(self, interaction: discord.Interaction) -> None:
        session = self.view.session
        if session is None or session.selected_index is None:
            await interaction.response.send_message("候補を選択してください。", ephemeral=True)
            return

        removed = session.delete_selected()
        await self.view.render(interaction, status_message=f"「{removed}」を削除しました。")


class _SaveButton(discord.ui.Button):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(style=discord.ButtonStyle.success, label="変更を保存")

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.view.session is None:
            await interaction.response.send_message("テンプレートを選択してください。", ephemeral=True)
            return

        message = await self.view.save_changes(interaction)
        await self.view.render(interaction, status_message=message)


class _DiscardButton(discord.ui.Button):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="変更を破棄")

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.view.session is None:
            await interaction.response.send_message("テンプレートを選択してください。", ephemeral=True)
            return

        template = self.view.templates.get(self.view.session.template_id)
        if template is None:
            await interaction.response.send_message("テンプレートが見つかりません。", ephemeral=True)
            return

        self.view.session.reset_with(template)
        await self.view.render(interaction, status_message="変更を破棄しました。")


class _DeleteTemplateButton(discord.ui.Button):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(style=discord.ButtonStyle.danger, label="テンプレートを削除")

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.view.session is None:
            await interaction.response.send_message("テンプレートを選択してください。", ephemeral=True)
            return

        modal = _DeleteTemplateModal(self.view)
        await interaction.response.send_modal(modal)


class _CloseButton(discord.ui.Button):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="閉じる")

    async def callback(self, interaction: discord.Interaction) -> None:
        for child in self.view.children:
            child.disabled = True
        await self.view.render(interaction, status_message="テンプレート管理を終了しました。")
        self.view.stop()


class _RenameTitleModal(discord.ui.Modal):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(title="テンプレート名の編集", timeout=300)
        self.template_view = view
        session = view.session
        default = session.title if session else ""
        self.title_input = discord.ui.TextInput(
            label="新しいタイトル",
            default=default,
            min_length=1,
            max_length=100,
        )
        self.add_item(self.title_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.template_view.session is None:
            await interaction.response.send_message("テンプレートが選択されていません。", ephemeral=True)
            return

        new_title = self.title_input.value.strip()
        self.template_view.session.title = new_title
        await self.template_view.render(interaction, status_message="タイトルを更新しました。")


class _AddOptionModal(discord.ui.Modal):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(title="候補を追加", timeout=300)
        self.template_view = view
        self.option_input = discord.ui.TextInput(
            label="候補名",
            placeholder="新しい候補を入力",
            min_length=1,
            max_length=100,
        )
        self.add_item(self.option_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.template_view.session is None:
            await interaction.response.send_message("テンプレートが選択されていません。", ephemeral=True)
            return

        option_name = self.option_input.value.strip()
        self.template_view.session.add_choice(option_name)
        await self.template_view.render(interaction, status_message=f"「{option_name}」を追加しました。")


class _RenameOptionModal(discord.ui.Modal):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(title="候補名の編集", timeout=300)
        self.template_view = view
        session = view.session
        current_value = ""
        if session and session.selected_index is not None:
            current_value = session.choices[session.selected_index]
        self.option_input = discord.ui.TextInput(
            label="新しい候補名",
            default=current_value,
            min_length=1,
            max_length=100,
        )
        self.add_item(self.option_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        session = self.template_view.session
        if session is None or session.selected_index is None:
            await interaction.response.send_message("候補が選択されていません。", ephemeral=True)
            return

        new_value = self.option_input.value.strip()
        session.rename_choice(new_value)
        await self.template_view.render(
            interaction,
            status_message=f"候補を「{new_value}」に更新しました。",
        )


class _DeleteTemplateModal(discord.ui.Modal):
    def __init__(self, view: TemplateManagementView) -> None:
        super().__init__(title="テンプレート削除の確認", timeout=300)
        self.template_view = view
        self.confirm_input = discord.ui.TextInput(
            label="確認キーワード",
            placeholder="削除と入力してください",
            min_length=2,
            max_length=16,
        )
        self.add_item(self.confirm_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.template_view.session is None:
            await interaction.response.send_message("テンプレートが選択されていません。", ephemeral=True)
            return

        if self.confirm_input.value.strip() != "削除":
            await interaction.response.send_message("確認キーワードが一致しません。", ephemeral=True)
            return

        message = await self.template_view.delete_current_template(interaction)
        await self.template_view.render(interaction, status_message=message)
