import discord

from data_interface import DataInterface
from db_manager import db
from model.context_model import CommandContext
from model.model import Template
from model.state_model import AmidakujiState


class UseExistingButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="既存のテンプレート")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.MODE_USE_EXISTING,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class CreateNewButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.success, label="テンプレートを作成")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.MODE_CREATE_NEW,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


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


class EnterOptionButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="次のステップ")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.ENTER_OPTION_BUTTON_CLICKED,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class NeedMoreOptionsButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="さらにオプションを入力"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.NEED_MORE_OPTIONS,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class ApplyOptionsButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(style=discord.ButtonStyle.primary, label="テンプレートを保存")
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        template = Template(
            title=self.context.history[AmidakujiState.TEMPLATE_TITLE_ENTERED],
            choices=self.context.history[AmidakujiState.OPTION_NAME_ENTERED],
        )

        self.context.update_context(
            state=AmidakujiState.TEMPLATE_CREATED,
            result=template,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class UseHistoryButton(discord.ui.Button):
    def __init__(self, context: CommandContext):
        super().__init__(
            style=discord.ButtonStyle.secondary, label="最後に使ったテンプレート"
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        self.context.update_context(
            state=AmidakujiState.MODE_USE_HISTORY,
            result=interaction,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class TemplateSelect(discord.ui.Select):
    def __init__(self, context: CommandContext, templates: list[Template]):
        # templatesからSelectOptionを作成
        super().__init__(
            placeholder="テンプレートを選択してください",
            options=[
                discord.SelectOption(label=template.title) for template in templates
            ],
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        # 取得した値を元にテンプレートを取得
        selected_template_title = self.values[0]
        current_user = db.get_user(interaction.user.id)
        user_templates = current_user.custom_templates
        selected_template = next(
            t for t in user_templates if t.title == selected_template_title
        )

        self.context.update_context(
            state=AmidakujiState.TEMPLATE_DETERMINED,
            result=selected_template,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class MemberSelect(discord.ui.UserSelect):
    def __init__(self, context: CommandContext):
        super().__init__(
            placeholder="あみだくじに参加するメンバーを選択してください",
            min_values=1,
            max_values=25,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        # Memberの可能性があるので、Userに変換(APIの仕様上、DM内ならUser, サーバー内ならMemberに統一されている)
        result = []
        for user in self.values:
            if isinstance(user, discord.User):
                result.append(user)
            elif isinstance(user, discord.Member):
                result.append(self.context.interaction.client.get_user(user.id))

        self.context.update_context(
            state=AmidakujiState.MEMBER_SELECTED,
            result=result,
            interaction=interaction,
        )

        interface = DataInterface(context=self.context)
        await interface.forward()


class MemberSelectView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(MemberSelect(context))


class SelectTemplateView(discord.ui.View):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(timeout=300)
        self.add_item(TemplateSelect(context, templates))


class EnterOptionView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(EnterOptionButton(context))


class ApplyOptionsView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(ApplyOptionsButton(context))
        self.add_item(NeedMoreOptionsButton(context))


class ModeSelectionView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(UseExistingButton(context))
        self.add_item(CreateNewButton(context))
        self.add_item(UseHistoryButton(context))
