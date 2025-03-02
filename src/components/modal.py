import discord

from data_interface import DataInterface
from model.context_model import CommandContext
from model.state_model import AmidakujiState


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
        self.context.update_context(
            state=AmidakujiState.TEMPLATE_TITLE_ENTERED,
            result=self.title_input.value,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


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
            # 二回目以降
            result = self.context.history[AmidakujiState.OPTION_NAME_ENTERED]
            result.append(self.option_name_input.value)

            self.context.update_context(
                state=AmidakujiState.OPTION_NAME_ENTERED,
                result=result,
                interaction=interaction,
            )
        else:
            # 初回入力
            result = [self.option_name_input.value]

            self.context.update_context(
                state=AmidakujiState.OPTION_NAME_ENTERED,
                result=result,
                interaction=interaction,
            )

        interface = DataInterface(context=self.context)
        await interface.forward()
