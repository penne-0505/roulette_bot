from __future__ import annotations
from enum import Enum, auto
from math import ceil
from typing import Iterable

import discord

from models.model import Template
from views.search_utils import TemplateSearchEntry, search_templates


class TemplateCategory(Enum):
    PRIVATE = auto()
    GUILD = auto()
    PUBLIC = auto()


CATEGORY_LABELS = {
    TemplateCategory.PRIVATE: "個人テンプレート",
    TemplateCategory.GUILD: "サーバー共有",
    TemplateCategory.PUBLIC: "グローバル公開",
}

class TemplateListView(discord.ui.View):
    """テンプレートの一覧をカテゴリ別に切り替えて表示するビュー。"""

    PAGE_SIZE = 6

    def __init__(
        self,
        *,
        private_templates: Iterable[Template],
        guild_templates: Iterable[Template],
        public_templates: Iterable[Template],
    ) -> None:
        super().__init__(timeout=180)
        self.templates = {
            TemplateCategory.PRIVATE: list(private_templates),
            TemplateCategory.GUILD: list(guild_templates),
            TemplateCategory.PUBLIC: list(public_templates),
        }
        self.current_category: TemplateCategory = self._resolve_initial_category()
        self.current_page: int = 0
        self.is_search_mode: bool = False
        self.search_query: str | None = None
        self.search_results: list[TemplateSearchEntry] = []

        self.category_buttons = [
            _CategoryButton(self, TemplateCategory.PRIVATE, "個人"),
            _CategoryButton(self, TemplateCategory.GUILD, "共有"),
            _CategoryButton(self, TemplateCategory.PUBLIC, "公開"),
        ]
        for button in self.category_buttons:
            self.add_item(button)

        self.prev_button = _PageButton(self, label="前へ", delta=-1)
        self.next_button = _PageButton(self, label="次へ", delta=1)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)

        self.search_button = _SearchButton(self)
        self.add_item(self.search_button)

        self.reset_search_button = _ResetSearchButton(self)
        self.add_item(self.reset_search_button)

        self.close_button = _CloseButton(self)
        self.add_item(self.close_button)

        self._update_components()

    def _resolve_initial_category(self) -> TemplateCategory:
        for category in TemplateCategory:
            if self.templates.get(category):
                return category
        return TemplateCategory.PRIVATE

    def _update_components(self) -> None:
        total_pages = self._total_pages_for(self.current_category)
        if self.is_search_mode:
            for button in self.category_buttons:
                button.disabled = True
                button.style = discord.ButtonStyle.secondary
        else:
            for button in self.category_buttons:
                button.disabled = button.category is self.current_category
                button.style = (
                    discord.ButtonStyle.primary
                    if button.category is self.current_category
                    else discord.ButtonStyle.secondary
                )
        disable_paging = total_pages <= 1 or (
            self.is_search_mode and not self.search_results
        )
        self.prev_button.disabled = disable_paging or self.current_page <= 0
        self.next_button.disabled = (
            disable_paging or self.current_page >= total_pages - 1
        )
        self.reset_search_button.disabled = not self.is_search_mode

    def _total_pages_for(self, category: TemplateCategory | None) -> int:
        if self.is_search_mode:
            items: list[TemplateSearchEntry] = self.search_results
        else:
            target = category or self.current_category
            items = self.templates.get(target, [])
        if not items:
            return 1
        return ceil(len(items) / self.PAGE_SIZE)

    def _current_items(self) -> list[Template]:
        if self.is_search_mode:
            return []
        items = self.templates.get(self.current_category, [])
        if not items:
            return []
        start = self.current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        return items[start:end]

    def _current_search_entries(self) -> list[TemplateSearchEntry]:
        if not self.search_results:
            return []
        start = self.current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        return self.search_results[start:end]

    def _format_template(self, template: Template, index: int) -> str:
        choices = ", ".join(template.choices[:8]) if template.choices else "候補なし"
        if template.choices and len(template.choices) > 8:
            choices += ", ..."
        scope_note = ""
        if template.scope:
            scope_note = f"（scope: {template.scope.value}）"
        prefix = f"{index}. "
        return f"{prefix}**{template.title}**{scope_note}\n`{choices}`"

    def _format_search_result(
        self, entry: TemplateSearchEntry, index: int
    ) -> str:
        base = self._format_template(entry.template, index)
        details: list[str] = []
        if entry.matched_keywords:
            keywords = ", ".join(sorted(set(entry.matched_keywords)))
            details.append(f"一致語: {keywords}")
        details.append(f"スコア: {entry.score:.2f}")
        detail_text = " / ".join(details)
        return f"{base}\n{detail_text}"

    def create_embed(self) -> discord.Embed:
        if self.is_search_mode:
            label = "検索結果"
            description = f"キーワード: {self.search_query}"
            total_items = len(self.search_results)
            entries = self._current_search_entries()
            embed = discord.Embed(
                title="利用可能なテンプレート",
                description=f"{label} - {description}",
                color=discord.Color.blurple(),
            )
            if not entries:
                embed.add_field(
                    name="検索結果",
                    value="条件に一致するテンプレートが見つかりませんでした。",
                    inline=False,
                )
            else:
                lines = [
                    self._format_search_result(
                        entry, index + 1 + self.current_page * self.PAGE_SIZE
                    )
                    for index, entry in enumerate(entries)
                ]
                embed.add_field(
                    name="検索結果",
                    value="\n\n".join(lines),
                    inline=False,
                )
            total_pages = self._total_pages_for(None)
            embed.set_footer(
                text=(
                    f"{label}: {total_items}件 | ページ {self.current_page + 1}/{total_pages}"
                )
            )
            return embed

        label = CATEGORY_LABELS[self.current_category]
        embed = discord.Embed(
            title="利用可能なテンプレート",
            description=f"カテゴリ: {label}",
            color=discord.Color.blurple(),
        )
        items = self._current_items()
        total_items = len(self.templates.get(self.current_category, []))
        if not items:
            embed.add_field(name="テンプレート", value="対象のテンプレートが見つかりません。", inline=False)
        else:
            lines = [
                self._format_template(template, index + 1 + self.current_page * self.PAGE_SIZE)
                for index, template in enumerate(items)
            ]
            embed.add_field(name="テンプレート", value="\n\n".join(lines), inline=False)

        total_pages = self._total_pages_for(self.current_category)
        embed.set_footer(
            text=(
                f"{label}: {total_items}件 | ページ {self.current_page + 1}/{total_pages}"
            )
        )
        return embed

    async def render(self, interaction: discord.Interaction) -> None:
        self._update_components()
        embed = self.create_embed()
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    def set_category(self, category: TemplateCategory) -> None:
        if self.current_category is category:
            return
        self.current_category = category
        self.current_page = 0

    def turn_page(self, delta: int) -> None:
        total_pages = self._total_pages_for(self.current_category)
        self.current_page = max(0, min(self.current_page + delta, total_pages - 1))

    def enter_search_mode(self, query: str, results: list[TemplateSearchEntry]) -> None:
        self.is_search_mode = True
        self.search_query = query
        self.search_results = results
        self.current_page = 0

    def reset_search_mode(self) -> None:
        if not self.is_search_mode:
            return
        self.is_search_mode = False
        self.search_query = None
        self.search_results = []
        self.current_page = 0

    async def handle_search_submission(
        self, raw_query: str, interaction: discord.Interaction
    ) -> None:
        query = raw_query.strip()
        if not query:
            await interaction.response.send_message(
                "空白のみのキーワードは利用できません。", ephemeral=True
            )
            return
        results = search_templates(self._all_templates(), query)
        self.enter_search_mode(query, results)
        await self.render(interaction)

    def _all_templates(self) -> list[Template]:
        seen: set[str] = set()
        collected: list[Template] = []
        for category in TemplateCategory:
            for template in self.templates.get(category, []):
                identifier = template.template_id or template.title
                if identifier in seen:
                    continue
                seen.add(identifier)
                collected.append(template)
        return collected

    async def close(self, interaction: discord.Interaction) -> None:
        self.stop()
        editor = (
            interaction.edit_original_response
            if interaction.response.is_done()
            else interaction.response.edit_message
        )
        await editor(view=None)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True


class _CategoryButton(discord.ui.Button):
    def __init__(
        self,
        view: TemplateListView,
        category: TemplateCategory,
        label: str,
    ) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.view_instance = view
        self.category = category

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        view = self.view_instance
        view.set_category(self.category)
        await view.render(interaction)


class _PageButton(discord.ui.Button):
    def __init__(self, view: TemplateListView, *, label: str, delta: int) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.view_instance = view
        self.delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        view = self.view_instance
        if self.disabled:
            await interaction.response.defer(thinking=False)
            return
        view.turn_page(self.delta)
        await view.render(interaction)


class _SearchButton(discord.ui.Button):
    def __init__(self, view: TemplateListView) -> None:
        super().__init__(label="検索", style=discord.ButtonStyle.primary)
        self.view_instance = view

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        modal = TemplateSearchModal(self.view_instance)
        await interaction.response.send_modal(modal)


class _ResetSearchButton(discord.ui.Button):
    def __init__(self, view: TemplateListView) -> None:
        super().__init__(label="一覧に戻る", style=discord.ButtonStyle.secondary, disabled=True)
        self.view_instance = view

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        view = self.view_instance
        if not view.is_search_mode:
            await interaction.response.defer(thinking=False)
            return
        view.reset_search_mode()
        await view.render(interaction)


class TemplateSearchModal(discord.ui.Modal):
    def __init__(self, view: TemplateListView) -> None:
        super().__init__(title="テンプレート検索")
        self.view_instance = view
        self.query = discord.ui.TextInput(
            label="検索キーワード",
            placeholder="例: 誕生日 抽選",
            min_length=1,
            max_length=100,
        )
        self.add_item(self.query)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.view_instance.handle_search_submission(str(self.query.value), interaction)


class _CloseButton(discord.ui.Button):
    def __init__(self, view: TemplateListView) -> None:
        super().__init__(label="閉じる", style=discord.ButtonStyle.danger)
        self.view_instance = view

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        await self.view_instance.close(interaction)
