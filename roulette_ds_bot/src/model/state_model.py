from enum import Enum, auto
from typing import TypedDict

import discord
from model import Template


class AmidakujiStateValues(TypedDict, total=False):
    COMMAND_EXECUTED: discord.Interaction

    MODE_USE_EXISTING: discord.Interaction
    MODE_CREATE_NEW: discord.Interaction
    MODE_USE_HISTORY: discord.Interaction

    TEMPLATE_TITLE_ENTERED: str
    OPTIONS_COUNT_ENTERED: int
    NEED_MORE_OPTIONS: discord.Interaction
    TEMPLATE_CREATED: Template

    TEMPLATE_DETERMINED: Template

    MEMBER_SELECTED: list[discord.User]

    RESULT_DISPLAYED: discord.Interaction

    HISTORY_SAVED: discord.Interaction

    CANCELLED: discord.Interaction


class AmidakujiState(Enum):
    """
    あみだくじコマンドの処理、処理フローを進行するときに使う。
    """

    COMMAND_EXECUTED = auto()  # この状態の時、基本的にインターフェイスに渡すことは無い

    # コマンドを実行したときに、これらのボタンが表示される
    MODE_USE_EXISTING = auto()  # 既存のテンプレートを使用
    MODE_CREATE_NEW = auto()  # テンプレート新規作成
    MODE_USE_HISTORY = auto()  # 履歴を使用

    # このブロックは、テンプレート新規作成特有
    TEMPLATE_TITLE_ENTERED = auto()  # テンプレートのタイトルが入力された時
    OPTIONS_COUNT_ENTERED = auto()  # オプション数の入力が終わった時
    NEED_MORE_OPTIONS = auto()  # 事前指定したオプション数を満たしておらず、もう一度モーダルを表示する必要がある時
    TEMPLATE_CREATED = auto()  # dbに保存する必要があるため、別途ステップを追加

    TEMPLATE_DETERMINED = auto()  # 履歴使用、既存使用、新規作成すべてが、最終的にテンプレートが決定したときにこれを使う

    MEMBER_SELECTED = auto()  # これもすべてが共通して使う

    RESULT_DISPLAYED = (
        auto()
    )  # 結果を表示し終わった時。次のステップでdbに履歴を保存する

    HISTORY_SAVED = auto()  # これがゴール

    CANCELLED = (
        auto()
    )  # キャンセルボタンなどが押された時。interactionを破棄して操作を終了する
