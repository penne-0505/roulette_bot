from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import discord
import utils


class AmidakujiState(Enum):
    '''
    あみだくじコマンドの処理、処理フローを進行するときに使う。
    '''
    # コマンドを実行したときに、これらのボタンが表示される
    MODE_USE_EXISTING = auto() # 既存のテンプレートを使用
    MODE_CREATE_NEW = auto() # テンプレート新規作成
    MODE_USE_HISTORY = auto() # 履歴を使用
    
    # このブロックは、テンプレート新規作成特有
    TEMPLATE_TITLE_ENTERED = auto() # テンプレートのタイトルが入力された時
    OPTIONS_COUNT_ENTERED = auto() # オプション数の入力が終わった時
    NEED_MORE_OPTIONS = auto() # 事前指定したオプション数を満たしておらず、もう一度モーダルを表示する必要がある時
    TEMPLATE_CREATED = auto() # dbに保存する必要があるため、別途ステップを追加

    TEMPLATE_DETERMINED = auto() # 履歴使用、既存使用、新規作成すべてが、最終的にテンプレートが決定したときにこれを使う
    
    MEMBER_SELECTED = auto() # これもすべてが共通して使う

    RESULT_DISPLAYED = auto() # 結果を表示し終わった時。次のステップでdbに履歴を保存する

    HISTORY_SAVED = auto() # これがゴール



@dataclass
class CommandContext:
    '''
    要素間で情報を受け渡したり、次のステップを明示的にするために使う。
    '''
    interaction: discord.Interaction
    state: AmidakujiState
    result: Any
    history: dict[AmidakujiState, Any] = field(default_factory=dict)

    def add_to_history(self, state: AmidakujiState, result: Any):
        self.history[state] = result


@dataclass
class Template:
    '''
    テンプレートのデータモデル。DBに保存するときもこの形式を使う。
    '''
    title: str
    id: str = field(default_factory=lambda: None)  # 初期値をNoneに設定
    choices: list[str]

    def __post_init__(self):
        if self.id is None:
            self.id = utils.gen_template_id(self.title)


@dataclass
class UserInfo:
    '''
    DBに保存することを前提としたデータモデル。
    DBにわたす時にこの形式に直し、DBから受け取ったユーザー情報、テンプレート情報はこの形式で保持する
    '''
    id: int
    name: str
    least_template: Template | None = field(default=None)
    custom_templates: list[Template] = field(default_factory=list)


if __name__ == "__main__":
    pass
