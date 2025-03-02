import discord

from components.button import (
    ApplyOptionsButton,
    CreateNewButton,
    EnterOptionButton,
    NeedMoreOptionsButton,
    UseExistingButton,
    UseHistoryButton,
)
from components.select import MemberSelect, TemplateSelect
from model.context_model import CommandContext
from model.model import Template


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
