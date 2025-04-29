from dataclasses import dataclass, field
from typing import Any

import discord

from data_types.context_result_types import AmidakujiStateTypes, TypeRegistry
from models.state_model import AmidakujiState


@dataclass
class CommandContext:
    interaction: discord.Interaction
    state: AmidakujiState
    _result: AmidakujiStateTypes.EXPECTED_TYPES = field(default=None)
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
