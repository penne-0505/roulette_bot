from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import discord

from data_types.context_result_types import AmidakujiStateTypes, TypeRegistry
from models.state_model import AmidakujiState


@dataclass
class CommandContext:
    """
    要素間で情報を受け渡したり、次のステップを明示的にするために使う。
    コマンドの実行から全ての処理終了まで、同じインスタンスを使い続ける想定
    """

    interaction: discord.Interaction
    state: AmidakujiState
    services: Any | None = None
    _result: AmidakujiStateTypes.EXPECTED_TYPES = field(default=None)
    _history: dict[AmidakujiState, AmidakujiStateTypes.EXPECTED_TYPES] = field(
        default_factory=dict
    )
    options_snapshot: list[str] = field(default_factory=list)
    option_edit_index: int | None = None

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
        if not TypeRegistry().validate(state, result):
            raise TypeError(
                f"Invalid result type: {type(result)} expected: {TypeRegistry().get_type(state)}"
            )

    def update_context(
        self,
        state: AmidakujiState,
        result: AmidakujiStateTypes.EXPECTED_TYPES,
        interaction: discord.Interaction | None,
    ) -> None:
        if interaction is None:
            pass
        else:
            self.interaction = interaction
        self.state = state
        self.result = result

    def set_option_snapshot(
        self,
        options: Sequence[str],
        *,
        select_last: bool = False,
        preferred_index: int | None = None,
    ) -> None:
        normalized = list(options)
        self.options_snapshot = normalized
        self._history[AmidakujiState.OPTION_NAME_ENTERED] = list(normalized)

        if not normalized:
            self.option_edit_index = None
            return

        if preferred_index is not None:
            target_index = preferred_index
        elif select_last or self.option_edit_index is None:
            target_index = len(normalized) - 1
        else:
            target_index = self.option_edit_index

        target_index = max(0, min(target_index, len(normalized) - 1))
        self.option_edit_index = target_index
