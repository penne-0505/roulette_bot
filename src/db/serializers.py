"""Firestoreのドキュメントとアプリ内部モデル間の変換処理。"""
from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Mapping

from models.model import (
    AssignmentEntry,
    AssignmentHistory,
    SelectionMode,
    Template,
    TemplateScope,
)


def ensure_datetime(value: Any) -> datetime | None:
    """`datetime` か ISO8601文字列を `datetime` に正規化する。"""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def serialize_template(template: Template) -> dict[str, Any]:
    """テンプレートをFirestoreに保存しやすい辞書形式へ変換する。"""

    updated_at = template.updated_at or datetime.now(UTC)
    if template.updated_at is None:
        template.updated_at = updated_at

    data: dict[str, Any] = {
        "title": template.title,
        "choices": list(template.choices),
        "scope": template.scope.value,
        "updated_at": updated_at.isoformat(),
    }
    if template.created_by is not None:
        data["created_by"] = template.created_by
    if template.guild_id is not None:
        data["guild_id"] = template.guild_id
    if template.template_id is not None:
        data["template_id"] = template.template_id
    return data


def deserialize_template(data: Mapping[str, Any]) -> Template:
    """Firestoreから取得したテンプレート情報をモデルへ復元する。"""

    if not isinstance(data.get("title"), str):
        raise ValueError("Invalid template data: missing title")

    choices = data.get("choices")
    if not isinstance(choices, list) or not all(isinstance(choice, str) for choice in choices):
        raise ValueError("Invalid template data: choices must be list[str]")

    scope_value = data.get("scope")
    try:
        scope = TemplateScope(scope_value) if scope_value else TemplateScope.PRIVATE
    except ValueError:
        scope = TemplateScope.PRIVATE

    updated_at = ensure_datetime(data.get("updated_at"))
    template_id = data.get("template_id") or data.get("id")

    return Template(
        title=data["title"],
        choices=list(choices),
        scope=scope,
        created_by=data.get("created_by"),
        guild_id=data.get("guild_id"),
        template_id=template_id,
        updated_at=updated_at,
    )


def normalize_template_for_user(template: Template, user_id: int) -> Template:
    """ユーザーのプライベートテンプレートとして保存できる形式へ調整する。"""

    return replace(
        template,
        scope=TemplateScope.PRIVATE,
        created_by=user_id,
        guild_id=None,
        template_id=None,
    )


def deserialize_assignment_history(data: Mapping[str, Any]) -> AssignmentHistory:
    """Firestoreの履歴ドキュメントを `AssignmentHistory` に変換する。"""

    selection_mode_value = data.get("selection_mode", SelectionMode.RANDOM.value)
    if isinstance(selection_mode_value, SelectionMode):
        selection_mode = selection_mode_value
    else:
        try:
            selection_mode = SelectionMode(str(selection_mode_value))
        except ValueError:
            selection_mode = SelectionMode.RANDOM

    created_at_raw = data.get("created_at")
    created_at = ensure_datetime(created_at_raw)
    if created_at is None:
        raise ValueError("Invalid history timestamp")

    entries_raw = data.get("entries")
    if not isinstance(entries_raw, list):
        raise ValueError("Invalid history entries")

    entries = [
        AssignmentEntry(
            user_id=entry["user_id"],
            user_name=entry.get("user_name", ""),
            choice=entry["choice"],
        )
        for entry in entries_raw
        if isinstance(entry, Mapping)
    ]

    return AssignmentHistory(
        guild_id=data["guild_id"],
        template_title=data["template_title"],
        created_at=created_at,
        entries=entries,
        choices=list(data.get("choices", [])),
        selection_mode=selection_mode,
    )


__all__ = [
    "ensure_datetime",
    "serialize_template",
    "deserialize_template",
    "normalize_template_for_user",
    "deserialize_assignment_history",
]
