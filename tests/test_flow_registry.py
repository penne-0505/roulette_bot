from __future__ import annotations

import pytest

from flow.handlers import BaseStateHandler
from flow.registry import FlowHandlerRegistry
from models.state_model import AmidakujiState


class _DummyHandler(BaseStateHandler):
    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    async def handle(self, context, services):
        self.calls.append((context, services))
        return None


def test_registry_resolves_same_instance_per_state():
    registry = FlowHandlerRegistry(
        default_factories={AmidakujiState.MODE_CREATE_NEW: _DummyHandler}
    )

    first = registry.resolve(AmidakujiState.MODE_CREATE_NEW)
    second = registry.resolve(AmidakujiState.MODE_CREATE_NEW)

    assert isinstance(first, _DummyHandler)
    assert first is second


def test_registry_register_accepts_instances():
    registry = FlowHandlerRegistry(default_factories={})
    handler = _DummyHandler()
    registry.register(AmidakujiState.CANCELLED, handler)

    resolved = registry.resolve(AmidakujiState.CANCELLED)
    assert resolved is handler


def test_registry_raises_for_unknown_state():
    registry = FlowHandlerRegistry(default_factories={})

    with pytest.raises(KeyError):
        registry.resolve(AmidakujiState.MODE_USE_EXISTING)
