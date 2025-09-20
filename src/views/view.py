import discord

from components.button import (
    ApplyOptionsButton,
    BackToTemplateSelectButton,
    CreateNewButton,
    CopySharedTemplateButton,
    DeleteTemplateButton,
    EnterOptionButton,
    NeedMoreOptionsButton,
    UseExistingButton,
    UseHistoryButton,
    UsePublicTemplatesButton,
    UseSharedTemplateButton,
    UseSharedTemplatesButton,
)
from components.select import (
    MemberSelect,
    PublicTemplateSelect,
    SharedTemplateSelect,
    TemplateDeleteSelect,
    TemplateSelect,
)
from models.context_model import CommandContext
from models.model import Template


class MemberSelectView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(MemberSelect(context))


class SelectTemplateView(discord.ui.View):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(timeout=300)
        self.add_item(TemplateSelect(context, templates))
        self.add_item(DeleteTemplateButton(context, disabled=not templates))


class DeleteTemplateView(discord.ui.View):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(timeout=300)
        self.add_item(TemplateDeleteSelect(context, templates))
        self.add_item(BackToTemplateSelectButton(context))


class SharedTemplateSelectView(discord.ui.View):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(timeout=300)
        self.add_item(SharedTemplateSelect(context, templates))


class PublicTemplateSelectView(discord.ui.View):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(timeout=300)
        self.add_item(PublicTemplateSelect(context, templates))


class SharedTemplateActionView(discord.ui.View):
    def __init__(self, context: CommandContext, template: Template):
        super().__init__(timeout=300)
        self.add_item(UseSharedTemplateButton(context, template))
        self.add_item(CopySharedTemplateButton(context, template))


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
        self.add_item(UseSharedTemplatesButton(context))
        self.add_item(UsePublicTemplatesButton(context))
        self.add_item(UseHistoryButton(context))
