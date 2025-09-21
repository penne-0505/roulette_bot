from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from flow.actions import FlowAction
from flow.handlers.base import BaseStateHandler
from models.context_model import CommandContext


class CancelledHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction] | None:
        return None


__all__ = ["CancelledHandler"]
