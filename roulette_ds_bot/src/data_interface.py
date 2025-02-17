import data_process
from model.model import AmidakujiState, CommandContext, Template
import db_manager


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
                # dbからテンプレート取得 -> Templateインスタンス -> 選択のドロップダウンリスト表示(その後はUIのcallbackで)
                # dbからテンプレートを取得
                target_user = self.interaction.user
                fetched_user_data = self.db_manager.get_user(target_user.id)
                user_templates = fetched_user_data.custom_templates

                # テンプレートを
                
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
                    data_process.create_pair_from_list(selected_members, choices)
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
