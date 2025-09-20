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
    MODE_DELETE_TEMPLATE = auto()  # 既存のテンプレートを削除
    MODE_USE_SHARED = auto()  # 共有テンプレートを使用
    MODE_USE_PUBLIC = auto()  # 公開テンプレートを使用

    # このブロックは、テンプレート新規作成特有
    TEMPLATE_TITLE_ENTERED = auto()  # テンプレートのタイトルが入力された時
    ENTER_OPTION_BUTTON_CLICKED = auto()  # オプション入力ボタンが押された時(モーダルからモーダルは、ボタンを押すことで遷移する)
    OPTION_NAME_ENTERED = auto()  # オプションの名前が入力された時
    OPTION_MANAGE_SELECTED = auto()  # オプション管理ビューで選択が変更された時
    OPTION_DELETED = auto()  # オプションが削除された時
    OPTION_MOVED_UP = auto()  # オプションが上に移動された時
    OPTION_MOVED_DOWN = auto()  # オプションが下に移動された時
    NEED_MORE_OPTIONS = auto()  # さらにオプションを入力する必要がある時
    TEMPLATE_CREATED = auto()  # テンプレートが作成された時(dbに別途保存する必要がある)

    TEMPLATE_DETERMINED = auto()  # 履歴使用、既存使用、新規作成すべてが、最終的にテンプレートが決定したときにこれを使う

    TEMPLATE_DELETED = auto()  # テンプレートが削除されたときに使う
    SHARED_TEMPLATE_SELECTED = auto()  # 共有テンプレートが選択されたときに使う
    SHARED_TEMPLATE_COPY_REQUESTED = auto()  # 共有テンプレートのコピー要求

    MEMBER_SELECTED = auto()  # これもすべてが共通して使う

    CANCELLED = (
        auto()
    )  # キャンセルボタンなどが押された時。interactionを破棄して操作を終了する
