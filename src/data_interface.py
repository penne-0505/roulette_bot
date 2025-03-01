import discord

import data_process
from db_manager import db
from model.context_model import CommandContext
from model.model import Template
from model.state_model import AmidakujiState


class DataInterface:
    def __init__(self, context: CommandContext):
        self.context = context

    async def forward(self):
        from view_manager import MemberSelectView, SelectTemplateView

        match self.context.state:
            case AmidakujiState.MODE_USE_EXISTING:
                # dbからテンプレートを取得
                target_user = self.context.interaction.user
                fetched_user_data = db.get_user(target_user.id)
                user_templates = fetched_user_data.custom_templates

                # テンプレート選択viewを送信
                view = SelectTemplateView(
                    context=self.context, templates=user_templates
                )
                await self.context.interaction.response.send_message(
                    view=view, ephemeral=True
                )

            case AmidakujiState.MODE_CREATE_NEW:
                pass
            case AmidakujiState.TEMPLATE_TITLE_ENTERED:
                pass
            case AmidakujiState.OPTIONS_COUNT_ENTERED:
                pass
            case AmidakujiState.NEED_MORE_OPTIONS:
                pass
            case AmidakujiState.MODE_USE_HISTORY:
                # ユーザーの最後に使用したテンプレートを取得
                current_user = self.context.interaction.user
                user_least_template = db.get_user(current_user.id).least_template

                if not user_least_template:
                    embed = discord.Embed(
                        title="エラーが発生しました🥲",
                        description="履歴が見つかりませんでした。",
                        color=discord.Color.red(),
                    )
                    await self.context.interaction.response.send_message(
                        embed=embed, ephemeral=True
                    )
                    return

                embed = discord.Embed(
                    title=user_least_template.title,
                    description="このテンプレートを使用します。",
                )

                first_interaction = self.context.history[
                    AmidakujiState.COMMAND_EXECUTED
                ]

                await first_interaction.followup.send(embed=embed, ephemeral=True)

                self.context.update_context(
                    state=AmidakujiState.TEMPLATE_DETERMINED,
                    result=user_least_template,
                    interaction=self.context.interaction,
                )
                await self.forward()

            case AmidakujiState.TEMPLATE_DETERMINED:
                # dbに履歴を保存
                user_id = self.context.interaction.user.id
                db.set_least_template(user_id, self.context.result)

                # メンバー選択viewを送信
                view = MemberSelectView(context=self.context)
                await self.context.interaction.response.send_message(
                    view=view, ephemeral=True
                )

            case AmidakujiState.MEMBER_SELECTED:
                selected_members = self.context.result
                # コマンドコンテクストからテンプレートを取得
                selected_template = self.context.history[
                    AmidakujiState.TEMPLATE_DETERMINED
                ]
                choices = []
                if isinstance(selected_template, Template):
                    # ペアを作成
                    choices = selected_template.choices
                    result = data_process.create_pair_from_list(
                        selected_members, choices
                    )

                    embeds = data_process.create_embeds_from_pairs(
                        pairs=result, mode=db.get_embed_mode()
                    )

                    await self.context.interaction.response.send_message(
                        content=None,
                        embeds=embeds,
                    )
                else:
                    raise ValueError("Template is not selected")
            case _:
                raise ValueError("Invalid state")


if __name__ == "__main__":
    pass
