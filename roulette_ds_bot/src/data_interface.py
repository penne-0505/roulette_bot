import data_process
from model.model import AmidakujiState, CommandContext, Template


class DataInterface:
    def __init__(self, context: CommandContext):
        self.context = context
        self.interaction = self.context.interaction
        self.history = self.context.history
        self.result = self.context.result
        self.state = self.context.state

    def forward(self):
        match self.state:
            case AmidakujiState.MEMBER_SELECTED:
                selected_members = self.result
                selected_template = self.history[AmidakujiState.TEMPLATE_SELECTED]
                choices = []
                if isinstance(selected_template, Template):
                    choices = selected_template.choices
                    data_process.create_pair_from_list(selected_members, choices)
                else:
                    raise ValueError("Template is not selected")
            case AmidakujiState.MODE_USE_EXISTING:
                pass
            case AmidakujiState.MODE_CREATE_NEW:
                pass
            case AmidakujiState.MODE_USE_HISTORY:
                pass


if __name__ == "__main__":
    pass
