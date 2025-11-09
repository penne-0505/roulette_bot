"""Flow ハンドラの生成とキャッシュを担うレジストリ。"""
from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from typing import Protocol

from flow.handlers import (
    BaseStateHandler,
    CancelledHandler,
    CreateNewHandler,
    DeleteTemplateModeHandler,
    EnterOptionButtonHandler,
    MemberSelectedHandler,
    NeedMoreOptionsHandler,
    OptionDeletedHandler,
    OptionMovedDownHandler,
    OptionMovedUpHandler,
    OptionNameEnteredHandler,
    OptionSelectionChangedHandler,
    SharedTemplateCopyHandler,
    SharedTemplateSelectedHandler,
    TemplateCreatedHandler,
    TemplateDeletedHandler,
    TemplateDeterminedHandler,
    TemplateTitleEnteredHandler,
    UseExistingHandler,
    UseHistoryHandler,
    UsePublicTemplatesHandler,
    UseSharedTemplatesHandler,
)
from models.state_model import AmidakujiState


class _HandlerFactory(Protocol):
    def __call__(self) -> BaseStateHandler: ...


HandlerSpec = BaseStateHandler | _HandlerFactory


class FlowHandlerRegistry:
    """ステートに応じたハンドラインスタンスを遅延生成・共有するレジストリ。"""

    def __init__(
        self,
        default_factories: Mapping[AmidakujiState, HandlerSpec] | None = None,
        overrides: Mapping[AmidakujiState, HandlerSpec] | None = None,
    ) -> None:
        self._factories: MutableMapping[AmidakujiState, HandlerSpec] = (
            dict(default_factories or {})
        )
        if overrides:
            self._factories.update(overrides)
        self._instances: dict[AmidakujiState, BaseStateHandler] = {}

    def register(self, state: AmidakujiState, factory: HandlerSpec) -> None:
        """指定ステートのハンドラを上書き登録する（テスト/拡張用）。"""

        self._factories[state] = factory
        self._instances.pop(state, None)

    def resolve(self, state: AmidakujiState) -> BaseStateHandler:
        """ステートに対応するハンドラを取得する。"""

        if state in self._instances:
            return self._instances[state]

        factory = self._factories.get(state)
        if factory is None:
            raise KeyError(state)

        handler = self._build_handler(factory)
        self._instances[state] = handler
        return handler

    @staticmethod
    def _build_handler(factory: HandlerSpec) -> BaseStateHandler:
        if isinstance(factory, BaseStateHandler):
            return factory

        handler = factory()
        if not isinstance(handler, BaseStateHandler):
            raise TypeError("Handler factory must return a BaseStateHandler instance.")
        return handler


DEFAULT_HANDLER_FACTORIES: dict[AmidakujiState, HandlerSpec] = {
    AmidakujiState.MODE_USE_EXISTING: UseExistingHandler,
    AmidakujiState.MODE_CREATE_NEW: CreateNewHandler,
    AmidakujiState.MODE_USE_HISTORY: UseHistoryHandler,
    AmidakujiState.MODE_DELETE_TEMPLATE: DeleteTemplateModeHandler,
    AmidakujiState.MODE_USE_SHARED: UseSharedTemplatesHandler,
    AmidakujiState.MODE_USE_PUBLIC: UsePublicTemplatesHandler,
    AmidakujiState.TEMPLATE_TITLE_ENTERED: TemplateTitleEnteredHandler,
    AmidakujiState.ENTER_OPTION_BUTTON_CLICKED: EnterOptionButtonHandler,
    AmidakujiState.OPTION_NAME_ENTERED: OptionNameEnteredHandler,
    AmidakujiState.OPTION_MANAGE_SELECTED: OptionSelectionChangedHandler,
    AmidakujiState.OPTION_DELETED: OptionDeletedHandler,
    AmidakujiState.OPTION_MOVED_UP: OptionMovedUpHandler,
    AmidakujiState.OPTION_MOVED_DOWN: OptionMovedDownHandler,
    AmidakujiState.NEED_MORE_OPTIONS: NeedMoreOptionsHandler,
    AmidakujiState.TEMPLATE_CREATED: TemplateCreatedHandler,
    AmidakujiState.TEMPLATE_DELETED: TemplateDeletedHandler,
    AmidakujiState.TEMPLATE_DETERMINED: TemplateDeterminedHandler,
    AmidakujiState.MEMBER_SELECTED: MemberSelectedHandler,
    AmidakujiState.SHARED_TEMPLATE_SELECTED: SharedTemplateSelectedHandler,
    AmidakujiState.SHARED_TEMPLATE_COPY_REQUESTED: SharedTemplateCopyHandler,
    AmidakujiState.CANCELLED: CancelledHandler,
}


__all__ = [
    "FlowHandlerRegistry",
    "DEFAULT_HANDLER_FACTORIES",
    "HandlerSpec",
]
