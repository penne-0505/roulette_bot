from dataclasses import dataclass, field
from typing import Any, cast, get_args, get_type_hints

import discord
from model.model import TRUE_RESULT_TYPES
from state_model import AmidakujiState, AmidakujiStateValues


@dataclass
class CommandContext:
    """
    要素間で情報を受け渡したり、次のステップを明示的にするために使う。
    """

    interaction: discord.Interaction
    state: AmidakujiState
    result: TRUE_RESULT_TYPES
    _history: dict[AmidakujiState, TRUE_RESULT_TYPES] = field(default_factory=dict)

    @property
    def history(self) -> dict[AmidakujiState, Any]:
        """直接historyにアクセスすることを防ぐ"""
        raise AttributeError(
            "Cannot access history directly. Use get_typed_history instead."
        )

    @history.setter
    def history(self, value: Any) -> None:
        """直接historyに値をセットすることを防ぐ"""
        del value
        raise AttributeError("Cannot set history directly. Use add_to_history instead.")

    def add_to_history(self, state: AmidakujiState, result: Any) -> None:
        """
        状態と結果をhistoryに追加する。TypedDictを使用して型チェックを行う。
        """
        # AmidakujiStateValuesから期待される型を取得
        type_hints = get_type_hints(AmidakujiStateValues)
        expected_type = type_hints.get(state.name)

        if expected_type is None:
            raise ValueError(f"Unknown state: {state}")

        # 期待されているものが、Union型の場合(list[str], Optional[float]など)
        if hasattr(expected_type, "__origin__"):
            if expected_type.__origin__ is list:
                # list[discord.User]のようなものを期待していたが、そうでなかったとき
                if not isinstance(result, list):
                    raise TypeError(
                        f"{state.name} state expects list, got {type(result)}"
                    )

                # 期待されているタイプを取得
                element_type = get_args(expected_type)[0]
                # 一つでもresult内に想定外のタイプがあった場合
                if not all(isinstance(x, element_type) for x in result):
                    raise TypeError(
                        f"{state.name} state expects list of {element_type}, "
                        f"got list containing {[type(x) for x in result]}"
                    )
            else:
                # その他のUnion型の処理
                valid_types = get_args(expected_type)
                # 想定外のタイプだった場合
                if not isinstance(result, valid_types):
                    raise TypeError(
                        f"{state.name} state expects {expected_type}, "
                        f"got {type(result)}"
                    )
        # 通常の型の場合(str, intなど)かつ想定外だった場合
        elif not isinstance(result, expected_type):
            raise TypeError(
                f"{state.name} state expects {expected_type}, got {type(result)}"
            )

        # すべての型チェックに引っかからなかったら、historyに追加
        self.history[state] = result

    def _get_history(self, state: AmidakujiState) -> Any:
        """
        指定された状態の履歴を取得し、適切な型にキャストして返す。
        """
        if state not in self.history:
            raise KeyError(f"No history found for state: {state}")

        result = self.history[state]
        type_hints = get_type_hints(AmidakujiStateValues)
        expected_type = type_hints[state.name]

        return cast(expected_type, result)

    def get_typed_history(self, state: AmidakujiState) -> AmidakujiStateValues:
        """
        型安全な履歴取得のためのメソッド
        """
        return self._get_history(state)
