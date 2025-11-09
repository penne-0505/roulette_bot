import discord

from components.button import (
    ApplyOptionsButton,
    BackToTemplateSelectButton,
    CopySharedTemplateButton,
    EnterOptionButton,
    OptionDeleteButton,
    OptionMoveDownButton,
    OptionMoveUpButton,
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
from components.select import (
    MemberSelect,
    OptionManageSelect,
    TemplateDeleteSelect,
    TemplateSelect,
)
from domain import Template
from models.context_model import CommandContext


class MemberSelectView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(MemberSelect(context))


class SelectTemplateView(discord.ui.View):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(timeout=300)
        self.add_item(TemplateSelect(context, templates))


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
        options = list(context.options_snapshot)
        selected_index = context.option_edit_index

        if options:
            select = OptionManageSelect(
                context,
                options,
                selected_index=selected_index,
            )
            self.add_item(select)

        move_up = OptionMoveUpButton(context, row=1)
        move_down = OptionMoveDownButton(context, row=1)
        delete_button = OptionDeleteButton(context, row=2)

        if not options or selected_index is None:
            move_up.disabled = True
            move_down.disabled = True
            delete_button.disabled = True
        else:
            move_up.disabled = selected_index <= 0
            move_down.disabled = selected_index >= len(options) - 1


        self.add_item(move_up)
        self.add_item(move_down)
        self.add_item(delete_button)

        need_more = NeedMoreOptionsButton(context)
        need_more.row = 3
        self.add_item(need_more)

        apply_button = ApplyOptionsButton(context)
        apply_button.row = 3
        apply_button.disabled = len(options) < 2
        self.add_item(apply_button)


class ModeSelectionView(discord.ui.View):
    def __init__(self, context: CommandContext):
        super().__init__(timeout=300)
        self.add_item(UseExistingButton(context))
        self.add_item(UseSharedTemplatesButton(context))
        self.add_item(UsePublicTemplatesButton(context))
        self.add_item(UseHistoryButton(context))
