from __future__ import annotations

import datetime
from math import ceil
from typing import Iterable, Sequence

import discord

from db_manager import DBManager
from models.model import AssignmentHistory, SelectionMode, Template
from views.search_utils import search_templates


class HistoryListView(discord.ui.View):
    """抽選履歴をページングして閲覧するためのビュー。"""

    PAGE_SIZE_MIN = 1
    PAGE_SIZE_MAX = 10
    MAX_FETCH_LIMIT = 50
    PAGE_WINDOW = 5
    TEMPLATE_OPTION_LIMIT = 50
    MAX_MATCHED_TITLES = 5

    def __init__(
        self,
        *,
        db_manager: DBManager,
        guild_id: int,
        page_size: int = 5,
        template_title: str | None = None,
    ) -> None:
        super().__init__(timeout=180)
        self.db_manager = db_manager
        self.guild_id = guild_id
        self.page_size = self._normalize_page_size(page_size)
        self.template_query = self._normalize_query(template_title)
        self.strict_filter: bool = False
        self.strict_template_title: str | None = None
        self.matched_titles: list[str] = []
        self.current_page: int = 0
        self.histories: list[AssignmentHistory] = []
        self.available_templates: list[str] = []

        self.reload_data()

        self.prev_button = _HistoryPageButton(self, label="前へ", delta=-1)
        self.prev_button.row = 0
        self.add_item(self.prev_button)

        self.next_button = _HistoryPageButton(self, label="次へ", delta=1)
        self.next_button.row = 0
        self.add_item(self.next_button)

        self.reload_button = _HistoryReloadButton(self)
        self.reload_button.row = 0
        self.add_item(self.reload_button)

        self.template_select = _TemplateFilterSelect(self)
        self.template_select.row = 1
        self.add_item(self.template_select)

        self.template_modal_button = _TemplateFilterModalButton(self)
        self.template_modal_button.row = 3
        self.add_item(self.template_modal_button)

        self.page_size_select = _HistoryPageSizeSelect(self)
        self.page_size_select.row = 2
        self.add_item(self.page_size_select)

        self.reset_filter_button = _ResetHistoryFilterButton(self)
        self.reset_filter_button.row = 3
        self.add_item(self.reset_filter_button)

        self.close_button = _HistoryCloseButton(self)
        self.close_button.row = 3
        self.add_item(self.close_button)

        self._update_components()

    @staticmethod
    def _normalize_page_size(value: int) -> int:
        return max(
            HistoryListView.PAGE_SIZE_MIN,
            min(HistoryListView.PAGE_SIZE_MAX, value),
        )

    @staticmethod
    def _normalize_query(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def reload_data(self) -> None:
        fetch_limit = max(self.page_size * self.PAGE_WINDOW, self.TEMPLATE_OPTION_LIMIT)
        fetch_limit = min(fetch_limit, self.MAX_FETCH_LIMIT)

        base_histories = self.db_manager.get_recent_history(
            guild_id=self.guild_id,
            limit=fetch_limit,
        )

        self.available_templates = self._collect_template_titles(base_histories)

        candidate_templates = self._build_search_templates(base_histories)

        matched_titles: list[str] = []
        histories: list[AssignmentHistory]

        if self.template_query:
            entries = search_templates(candidate_templates, self.template_query)
            if self.strict_filter and self.strict_template_title:
                matched_titles = [self.strict_template_title]
            else:
                matched_titles = [
                    entry.template.title for entry in entries[: self.MAX_MATCHED_TITLES]
                ]
            matched_titles = [title for title in matched_titles if title]
            if not matched_titles and entries:
                matched_titles = [entries[0].template.title]

            aggregated: list[AssignmentHistory] = []
            for title in matched_titles:
                dedicated = self.db_manager.get_recent_history(
                    guild_id=self.guild_id,
                    template_title=title,
                    limit=self.MAX_FETCH_LIMIT,
                )
                aggregated.extend(dedicated)
            aggregated.sort(key=lambda item: item.created_at, reverse=True)
            histories = aggregated[: self.MAX_FETCH_LIMIT]
        else:
            histories = base_histories

        self.histories = histories
        self.matched_titles = matched_titles

        for title in reversed(matched_titles):
            if title and title not in self.available_templates:
                self.available_templates.insert(0, title)
        self.available_templates = self.available_templates[:25]

        total_pages = self._total_pages()
        if total_pages == 0:
            self.current_page = 0
        elif self.current_page >= total_pages:
            self.current_page = total_pages - 1

    def _collect_template_titles(
        self, histories: Iterable[AssignmentHistory]
    ) -> list[str]:
        seen: set[str] = set()
        titles: list[str] = []
        for history in histories:
            title = history.template_title
            if not title or title in seen:
                continue
            seen.add(title)
            titles.append(title)
        return titles[:25]

    def _build_search_templates(
        self, histories: Iterable[AssignmentHistory]
    ) -> list[Template]:
        seen: set[str] = set()
        templates: list[Template] = []
        for history in histories:
            title = history.template_title
            if not title or title in seen:
                continue
            seen.add(title)
            templates.append(
                Template(
                    title=title,
                    choices=list(history.choices or []),
                )
            )
        return templates

    def _total_pages(self) -> int:
        if not self.histories:
            return 0
        return ceil(len(self.histories) / self.page_size)

    def _current_histories(self) -> Sequence[AssignmentHistory]:
        if not self.histories:
            return []
        start = self.current_page * self.page_size
        end = start + self.page_size
        return self.histories[start:end]

    def turn_page(self, delta: int) -> None:
        if not self.histories:
            self.current_page = 0
            return
        total_pages = self._total_pages()
        target = max(0, min(self.current_page + delta, total_pages - 1))
        self.current_page = target

    def change_page_size(self, page_size: int) -> None:
        normalized = self._normalize_page_size(page_size)
        if self.page_size == normalized:
            return
        self.page_size = normalized
        self.current_page = 0
        self.reload_data()

    def apply_template_filter(self, template_title: str | None, *, strict: bool = False) -> None:
        normalized = self._normalize_query(template_title)
        if normalized is None:
            self.reset_template_filter()
            return
        self.template_query = normalized
        self.strict_filter = strict
        self.strict_template_title = normalized if strict else None
        self.current_page = 0
        self.reload_data()

    def reset_template_filter(self) -> None:
        if self.template_query is None and not self.strict_filter:
            return
        self.template_query = None
        self.strict_filter = False
        self.strict_template_title = None
        self.matched_titles = []
        self.current_page = 0
        self.reload_data()

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎲 最近の抽選履歴",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if self.template_query:
            if self.strict_filter and self.matched_titles:
                embed.description = f"テンプレート: {self.matched_titles[0]}"
            else:
                lines = [f"検索キーワード: {self.template_query}"]
                if self.matched_titles:
                    preview = ", ".join(self.matched_titles[:3])
                    if len(self.matched_titles) > 3:
                        preview += ", ..."
                    lines.append(f"候補: {preview}")
                else:
                    lines.append("候補が見つかりませんでした。")
                embed.description = "\n".join(lines)
        else:
            embed.description = "最新の抽選結果を表示します。"

        histories = self._current_histories()
        if not histories:
            embed.add_field(
                name="履歴",
                value="抽選履歴が見つかりませんでした。",
                inline=False,
            )
        else:
            for history in histories:
                field_name, field_value = self._format_history(history)
                embed.add_field(
                    name=field_name,
                    value=field_value,
                    inline=False,
                )

        total_pages = max(self._total_pages(), 1)
        total_entries = len(self.histories)
        footer_parts = [
            f"ページ {self.current_page + 1}/{total_pages}",
            f"読込済み {total_entries}件",
            f"1ページ {self.page_size}件",
        ]
        embed.set_footer(text=" | ".join(footer_parts))
        return embed

    @staticmethod
    def _format_history(history: AssignmentHistory) -> tuple[str, str]:
        selection_mode_label = {
            SelectionMode.RANDOM: "完全ランダム",
            SelectionMode.BIAS_REDUCTION: "偏り軽減",
        }.get(history.selection_mode, history.selection_mode.value)

        timestamp_text = history.created_at.astimezone(
            datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC")

        lines = [
            f"{entry.user_name} → {entry.choice}"
            for entry in history.entries
        ]
        value = "\n".join(lines) if lines else "記録がありません"
        if len(value) > 1024:
            value = value[:1010] + "\n..."

        field_name = (
            f"{history.template_title} ({timestamp_text}) [{selection_mode_label}]"
        )
        return field_name, value

    async def render(self, interaction: discord.Interaction) -> None:
        self._update_components()
        embed = self.create_embed()
        editor = (
            interaction.edit_original_response
            if interaction.response.is_done()
            else interaction.response.edit_message
        )
        await editor(embed=embed, view=self)

    async def close(self, interaction: discord.Interaction) -> None:
        self.stop()
        editor = (
            interaction.edit_original_response
            if interaction.response.is_done()
            else interaction.response.edit_message
        )
        await editor(view=None)

    def _update_components(self) -> None:
        total_pages = self._total_pages()
        has_histories = bool(self.histories)

        self.prev_button.disabled = not has_histories or self.current_page <= 0
        self.next_button.disabled = (
            not has_histories or total_pages <= 1 or self.current_page >= total_pages - 1
        )
        self.reset_filter_button.disabled = self.template_query is None and not self.strict_filter
        self.template_select.refresh_options()
        self.page_size_select.refresh_options()

        if not self.histories and not self.available_templates:
            self.template_select.disabled = True
        self.reload_button.disabled = False

    async def on_timeout(self) -> None:  # pragma: no cover - UI timeout
        for child in self.children:
            child.disabled = True


class _HistoryPageButton(discord.ui.Button):
    def __init__(self, view: HistoryListView, *, label: str, delta: int) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label=label)
        self._history_view = view
        self.delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        history_view = self._history_view
        history_view.turn_page(self.delta)
        await history_view.render(interaction)


class _HistoryReloadButton(discord.ui.Button):
    def __init__(self, view: HistoryListView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="再読み込み", emoji="🔄")
        self._history_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        history_view = self._history_view
        history_view.reload_data()
        await history_view.render(interaction)


class _TemplateFilterSelect(discord.ui.Select):
    def __init__(self, view: HistoryListView) -> None:
        super().__init__(
            placeholder="テンプレートで絞り込み",
            min_values=1,
            max_values=1,
            options=[],
        )
        self._history_view = view
        self.refresh_options()

    def refresh_options(self) -> None:
        history_view = self._history_view
        options: list[discord.SelectOption] = []
        for title in history_view.available_templates:
            options.append(
                discord.SelectOption(
                    label=title,
                    value=title,
                    default=(
                        history_view.strict_filter
                        and history_view.strict_template_title == title
                    ),
                )
            )
        if options:
            self.options = options
            self.disabled = False
        else:
            self.options = [
                discord.SelectOption(
                    label="利用可能なテンプレートがありません",
                    value="__no_templates__",
                    description="共有テンプレートや履歴が存在しません",
                )
            ]
            self.disabled = True

    async def callback(self, interaction: discord.Interaction) -> None:
        value = self.values[0]
        if value == "__no_templates__":
            await interaction.response.defer(ephemeral=True)
            return
        history_view = self._history_view
        history_view.apply_template_filter(value, strict=True)
        await history_view.render(interaction)


class _TemplateFilterModalButton(discord.ui.Button):
    def __init__(self, view: HistoryListView) -> None:
        super().__init__(style=discord.ButtonStyle.primary, label="テンプレート名を入力")
        self._history_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        modal = _TemplateFilterModal(self._history_view)
        await interaction.response.send_modal(modal)


class _TemplateFilterModal(discord.ui.Modal):
    def __init__(self, view: HistoryListView) -> None:
        super().__init__(title="テンプレート名で絞り込み")
        self._history_view = view
        self.template_input = discord.ui.TextInput(
            label="テンプレート名",
            placeholder="例: 2024年新年会",
            required=True,
            max_length=100,
            default=view.template_query or None,
        )
        self.add_item(self.template_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw_value = str(self.template_input.value or "")
        history_view = self._history_view
        history_view.apply_template_filter(raw_value, strict=False)
        await history_view.render(interaction)


class _HistoryPageSizeSelect(discord.ui.Select):
    def __init__(self, view: HistoryListView) -> None:
        super().__init__(
            placeholder="1ページの件数",
            min_values=1,
            max_values=1,
            options=[],
        )
        self._history_view = view
        self.refresh_options()

    def refresh_options(self) -> None:
        history_view = self._history_view
        options: list[discord.SelectOption] = []
        for size in range(
            HistoryListView.PAGE_SIZE_MIN, HistoryListView.PAGE_SIZE_MAX + 1
        ):
            options.append(
                discord.SelectOption(
                    label=f"{size}件ずつ表示",
                    value=str(size),
                    default=history_view.page_size == size,
                )
            )
        self.options = options

    async def callback(self, interaction: discord.Interaction) -> None:
        new_size = int(self.values[0])
        history_view = self._history_view
        history_view.change_page_size(new_size)
        await history_view.render(interaction)


class _ResetHistoryFilterButton(discord.ui.Button):
    def __init__(self, view: HistoryListView) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="絞り込み解除")
        self._history_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        history_view = self._history_view
        history_view.reset_template_filter()
        await history_view.render(interaction)


class _HistoryCloseButton(discord.ui.Button):
    def __init__(self, view: HistoryListView) -> None:
        super().__init__(style=discord.ButtonStyle.danger, label="閉じる")
        self._history_view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        history_view = self._history_view
        await history_view.close(interaction)


__all__ = ["HistoryListView"]
