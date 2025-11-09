"""Discord 向けの Embed コンポーネント群。"""
from __future__ import annotations

import discord

from domain import ResultEmbedMode, SelectionMode


def _embed_mode_label(mode: ResultEmbedMode) -> str:
    mapping = {
        ResultEmbedMode.COMPACT: "コンパクト",
        ResultEmbedMode.DETAILED: "詳細",
    }
    return mapping.get(mode, mode.value)


def create_embed_mode_overview_embed(mode: ResultEmbedMode) -> discord.Embed:
    label = _embed_mode_label(mode)
    embed = discord.Embed(
        title="現在の埋め込み表示形式",
        description=f"現在の表示形式: **{label}**",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="ボタンで変更するか、キャンセルできます。")
    return embed


def create_embed_mode_changed_embed(mode: ResultEmbedMode) -> discord.Embed:
    label = _embed_mode_label(mode)
    embed = discord.Embed(
        title="埋め込み表示形式を変更しました",
        description=f"現在の表示形式: **{label}**",
        color=discord.Color.green(),
    )
    return embed


def create_embed_mode_cancelled_embed(mode: ResultEmbedMode) -> discord.Embed:
    label = _embed_mode_label(mode)
    embed = discord.Embed(
        title="埋め込み表示形式の変更をキャンセルしました",
        description=f"現在の表示形式: **{label}**",
        color=discord.Color.light_grey(),
    )
    return embed


def _selection_mode_label(mode: SelectionMode) -> str:
    mapping = {
        SelectionMode.RANDOM: "完全ランダム",
        SelectionMode.BIAS_REDUCTION: "偏り軽減",
    }
    return mapping.get(mode, mode.value)


def create_selection_mode_overview_embed(mode: SelectionMode) -> discord.Embed:
    label = _selection_mode_label(mode)
    embed = discord.Embed(
        title="現在の抽選モード",
        description=f"現在の抽選方式: **{label}**",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="ボタンで変更するか、キャンセルできます。")
    return embed


def create_selection_mode_changed_embed(mode: SelectionMode) -> discord.Embed:
    label = _selection_mode_label(mode)
    embed = discord.Embed(
        title="抽選モードを変更しました",
        description=f"現在の抽選方式: **{label}**",
        color=discord.Color.green(),
    )
    return embed


def create_selection_mode_cancelled_embed(mode: SelectionMode) -> discord.Embed:
    label = _selection_mode_label(mode)
    embed = discord.Embed(
        title="抽選モードの変更をキャンセルしました",
        description=f"現在の抽選方式: **{label}**",
        color=discord.Color.light_grey(),
    )
    return embed


__all__ = [
    "create_embed_mode_overview_embed",
    "create_embed_mode_changed_embed",
    "create_embed_mode_cancelled_embed",
    "create_selection_mode_cancelled_embed",
    "create_selection_mode_changed_embed",
    "create_selection_mode_overview_embed",
]
