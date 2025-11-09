from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List

import pytest

from domain import AssignmentEntry, AssignmentHistory, SelectionMode
from presentation.discord.views.history_list import HistoryListView


@dataclass
class _DummyHistoryService:
    histories: List[AssignmentHistory]

    def get_recent_history(
        self,
        *,
        guild_id: int,
        template_title: str | None = None,
        limit: int = 10,
        since: datetime.datetime | None = None,
    ) -> List[AssignmentHistory]:
        del guild_id, since
        if template_title is None:
            candidates = list(self.histories)
        else:
            candidates = [
                history
                for history in self.histories
                if history.template_title == template_title
            ]
        sorted_candidates = sorted(
            candidates, key=lambda item: item.created_at, reverse=True
        )
        return sorted_candidates[:limit]


def _make_history(
    *,
    template_title: str,
    created_at: datetime.datetime,
    entries: list[AssignmentEntry],
    selection_mode: SelectionMode = SelectionMode.RANDOM,
) -> AssignmentHistory:
    return AssignmentHistory(
        guild_id=123,
        template_title=template_title,
        created_at=created_at,
        entries=entries,
        choices=["A", "B"],
        selection_mode=selection_mode,
    )


def _build_entries(seed: int) -> list[AssignmentEntry]:
    return [
        AssignmentEntry(user_id=seed, user_name=f"user-{seed}", choice="A"),
        AssignmentEntry(user_id=seed + 1, user_name=f"user-{seed + 1}", choice="B"),
    ]


@pytest.mark.asyncio
async def test_history_list_view_initial_state() -> None:
    base_time = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    histories = [
        _make_history(
            template_title="テンプレート3",
            created_at=base_time,
            entries=_build_entries(30),
            selection_mode=SelectionMode.BIAS_REDUCTION,
        ),
        _make_history(
            template_title="テンプレート2",
            created_at=base_time + datetime.timedelta(minutes=5),
            entries=_build_entries(20),
        ),
        _make_history(
            template_title="テンプレート1",
            created_at=base_time + datetime.timedelta(minutes=10),
            entries=_build_entries(10),
        ),
    ]
    history_service = _DummyHistoryService(histories)

    view = HistoryListView(
        history_service=history_service,
        guild_id=123,
        page_size=2,
    )

    embed = view.create_embed()

    assert embed.title == "🎲 最近の抽選履歴"
    assert len(embed.fields) == 2
    assert embed.fields[0].name.startswith("テンプレート1")
    assert "user-10" in embed.fields[0].value
    assert "ページ 1/2" in (embed.footer.text or "")

    assert view.available_templates == [
        "テンプレート1",
        "テンプレート2",
        "テンプレート3",
    ]
    assert any(
        option.default and option.value == str(view.page_size)
        for option in view.page_size_select.options
    )


@pytest.mark.asyncio
async def test_history_list_view_filtering() -> None:
    base_time = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    titles = ["テンプレートA", "テンプレートB", "テンプレートC"]
    histories = [
        _make_history(
            template_title=title,
            created_at=base_time + datetime.timedelta(minutes=idx),
            entries=_build_entries(idx * 10),
        )
        for idx, title in enumerate(titles)
    ]
    history_service = _DummyHistoryService(histories)

    view = HistoryListView(
        history_service=history_service,
        guild_id=123,
        page_size=3,
    )

    view.apply_template_filter("テンプレートB", strict=True)

    embed = view.create_embed()
    assert len(embed.fields) == 1
    assert embed.description == "テンプレート: テンプレートB"
    assert embed.fields[0].name.startswith("テンプレートB")

    view.apply_template_filter("テンプレ", strict=False)

    search_embed = view.create_embed()
    assert "検索キーワード: テンプレ" in (search_embed.description or "")
    assert "候補:" in (search_embed.description or "")
    for title in titles:
        assert title in (search_embed.description or "")
    assert len(search_embed.fields) == 3

    view.reset_template_filter()
    embed_after_reset = view.create_embed()
    assert "最新の抽選結果" in (embed_after_reset.description or "")
