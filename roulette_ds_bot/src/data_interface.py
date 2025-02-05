import data_process
from utils import AmidakujiState, CommandContext, Template


class DataInterface:
    def __init__(self, context: CommandContext):
        self.context = context
        self.interaction = self.context.interaction
        self.history = self.context.history
        self.result = self.context.result
        self.state = self.context.state

    def foward(self):
        match self.state:
            case AmidakujiState.MEMBER_SELECTED:
                selected_members = self.result
                selected_template = self.history[AmidakujiState.TEMPLATE_SELECTED]
                options = []
                if isinstance(selected_template, Template):
                    options = selected_template.options
                    data_process.create_pair_from_list(selected_members, options)
                else:
                    raise ValueError("Template is not selected")
            case AmidakujiState.MODE_SELECTED:
                selected_mode = self.result
                if selected_mode == "existing":
                    pass
                elif selected_mode == "new":
                    pass
                elif selected_mode == "history":
                    pass
                else:
                    raise ValueError("Invalid mode selected")
