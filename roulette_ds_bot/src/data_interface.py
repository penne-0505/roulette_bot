import data_process
import db_manager
from model.model import AmidakujiState, CommandContext, Template
from view_manager import SelectTemplateView


class DataInterface:
    def __init__(self, context: CommandContext):
        self.context = context
        self.interaction = self.context.interaction
        self.history = self.context.history
        self.result = self.context.result
        self.state = self.context.state
        self.db_manager = db_manager.DBManager()

    def forward(self):
        match self.state:
            case AmidakujiState.MODE_USE_EXISTING:
                # dbからテンプレートを取得
                target_user = self.interaction.user
                fetched_user_data = self.db_manager.get_user(target_user.id)
                user_templates = fetched_user_data.custom_templates

                # interactionに未応答だった場合、uiに起こして送信
                if not self.interaction.response.is_done():
                    view = SelectTemplateView(
                        context=self.context, templates=user_templates
                    )
                    self.interaction.response.send_message(view=view)
                else:
                    raise Exception(
                        "interactoin was done"
                    )  # TOOD: 適切なハンドリング実装

                pass
            case AmidakujiState.MODE_CREATE_NEW:
                pass
            case AmidakujiState.TEMPLATE_TITLE_ENTERED:
                pass
            case AmidakujiState.OPTIONS_COUNT_ENTERED:
                pass
            case AmidakujiState.NEED_MORE_OPTIONS:
                pass
            case AmidakujiState.MODE_USE_HISTORY:
                pass
            case AmidakujiState.MEMBER_SELECTED:
                selected_members = self.result
                # コマンドコンテクストからテンプレートを取得
                selected_template = self.history[AmidakujiState.TEMPLATE_DETERMINED]
                choices = []
                if isinstance(selected_template, Template):
                    # ペアを作成
                    choices = selected_template.choices
                    result = data_process.create_pair_from_list(
                        selected_members, choices
                    )
                    self.history[AmidakujiState.MEMBER_SELECTED] = result
                else:
                    raise ValueError("Template is not selected")
            case AmidakujiState.TEMPLATE_DETERMINED:
                pass
            case AmidakujiState.RESULT_DISPLAYED:
                pass
            case AmidakujiState.HISTORY_SAVED:
                pass
            case _:
                raise ValueError("Invalid state")


if __name__ == "__main__":
    pass
