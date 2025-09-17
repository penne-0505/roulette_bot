import discord

from models.context_model import CommandContext
from models.state_model import AmidakujiState


def _get_flow(context: CommandContext):
    services = context.services
    flow = getattr(services, "flow", None) if services is not None else None
    if flow is None:
        raise RuntimeError("Flow controller is not available")
    return flow


class TitleEnterModal(discord.ui.Modal):
    title_input = discord.ui.TextInput(
        placeholder="タイトルを入力してください",
        label="タイトル",
        style=discord.TextStyle.short,
        min_length=1,
        max_length=100,
    )

    def __init__(self, context: CommandContext):
        super().__init__(title="テンプレートのタイトルを入力してください", timeout=300)
        self.context = context

    async def on_submit(self, interaction: discord.Interaction):
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.TEMPLATE_TITLE_ENTERED,
            self.title_input.value,
            interaction,
        )


class OptionNameEnterModal(discord.ui.Modal):
    option_name_input = discord.ui.TextInput(
        placeholder="名前を入力してください",
        label="オプション",
        style=discord.TextStyle.short,
        min_length=1,
        max_length=100,
    )

    def __init__(self, context: CommandContext):
        super().__init__(title="オプションの名前を入力してください", timeout=300)
        self.context = context

    async def on_submit(self, interaction: discord.Interaction):
        if self.context.state == AmidakujiState.NEED_MORE_OPTIONS:
            result = self.context.history[AmidakujiState.OPTION_NAME_ENTERED]
            result.append(self.option_name_input.value)
        else:
            result = [self.option_name_input.value]

        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.OPTION_NAME_ENTERED,
            result,
            interaction,
        )
