from enum import Enum, auto


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

    CANCELLED = (
        auto()
    )  # キャンセルボタンなどが押された時。interactionを破棄して操作を終了する
