from dataclasses import dataclass, field
from typing import Any, get_type_hints

import discord
from data_type.context_result_types import AmidakujiStateTypes
from state_model import AmidakujiState


@dataclass
class CommandContext:
    """
    要素間で情報を受け渡したり、次のステップを明示的にするために使う。
    コマンドの実行から全ての処理終了まで、同じインスタンスを使い続ける想定
    """

    interaction: discord.Interaction
    state: AmidakujiState
    _result: AmidakujiStateTypes.EXPECTED_TYPES
    _history: dict[AmidakujiState, AmidakujiStateTypes.EXPECTED_TYPES] = field(
        default_factory=dict
    )

    @property
    def result(self) -> AmidakujiStateTypes.EXPECTED_TYPES:
        return self._result

    @property
    def history(self) -> dict[AmidakujiState, AmidakujiStateTypes.EXPECTED_TYPES]:
        return self._history

    @result.setter
    def result(self, value: AmidakujiStateTypes.EXPECTED_TYPES) -> None:
        self._check_result_type(self.state, value)
        self._result = value
        self.history[self.state] = value

    @history.setter
    def history(self, value: Any) -> None:
        # 直接historyに値をセットすることを防ぐ
        raise AttributeError(
            "You cannot directly edit the history. When you set a result, it is automatically added to the history."
        )

    def _check_result_type(self, state: AmidakujiState, result: Any) -> None:
        """
        resultのデータ型が正しいかチェックする。
        """
        expected_type = get_type_hints(AmidakujiStateTypes).get(state)
        if not isinstance(result, expected_type):
            raise TypeError(
                f"Invalid result type: {type(result)} expected: {expected_type}"
            )
