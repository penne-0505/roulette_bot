import asyncio
import datetime
import hashlib
import logging
import os
import time
from pathlib import Path
from types import SimpleNamespace

import discord
import psutil
from discord.app_commands import locale_str
from dotenv import load_dotenv

from data_interface import FlowController
from models.context_model import CommandContext
from models.model import SelectionMode
from models.state_model import AmidakujiState
from services.app_context import create_db_manager
from utils import (
    DATEFORMAT,
    FORMAT,
    INFO,
    CommandsTranslator,
    blue,
    bold,
    green,
    magenta,
    yellow,
)
from views.view import ModeSelectionView

intents = discord.Intents.all()

logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt=DATEFORMAT,
)

# TODO: テンプレート削除機能の実装 -> 別のstateを追加?


class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.start_time = time.time()
        self.db = create_db_manager()

    async def on_ready(self):
        # デフォルトテンプレートの初期化
        self.db._init_default_templates()

        # 以下ログ
        logging.info(
            INFO + f"Logged in as {green(self.user.name)} ({blue(self.user.id)})"
        )
        logging.info(INFO + f"Connected to {green(len(self.guilds))} guilds")
        logging.info(INFO + f"Launch time: {green(time.time() - self.start_time)}s")
        logging.info(INFO + bold("Bot is ready."))

    async def setup_hook(self) -> None:
        # コマンドの翻訳機能を設定
        await tree.set_translator(CommandsTranslator())
        await tree.sync()
        logging.info(INFO + "Application commands synchronized.")

    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command | discord.app_commands.ContextMenu,
    ):
        # コマンド実行時に、ユーザーがDBに登録されていない場合、登録する
        exec_user = interaction.user
        user_id = exec_user.id
        if not self.db.user_is_exist(user_id):
            self.db.init_user(user_id=user_id, name=exec_user.name)

        # 装飾してログを出力
        exec_guild = yellow(interaction.guild) if interaction.guild else "DM"
        exec_channel = magenta(interaction.channel) if interaction.channel else "(DM)"
        user_name = blue(exec_user.name)
        user_id = blue(exec_user.id)
        exec_command = green(command.name)
        logging.info(
            INFO
            + f"Command executed by {user_name}({user_id}): {exec_command} in {exec_guild}({exec_channel})"
        )


client = Client()
tree = discord.app_commands.CommandTree(client=client)


@tree.command(name=locale_str("ping"), description="Ping the bot. 🏓")
async def command_ping(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    # Websocketレイテンシ
    ws_latency = round(client.latency * 1000)

    # APIレイテンシ
    start_time = time.perf_counter()
    message = await interaction.followup.send("測定中...")
    end_time = time.perf_counter()
    api_latency = round((end_time - start_time) * 1000)

    # リソース使用量
    process = psutil.Process()
    memory_usage = process.memory_info().rss / 1024 / 1024  # MB
    cpu_usage = process.cpu_percent()

    embed = discord.Embed(
        title="🏓 Pong!", color=discord.Color.green(), timestamp=datetime.datetime.now()
    )

    # fmt: off
    embed.add_field(
        name="📡 Connection",
        value=(
            "```\n"
            f"Websocket: {ws_latency}ms\n"
            f"API: {api_latency}ms\n"
            "```"
        ),
        inline=False,
    )
    # fmt: on

    embed.add_field(
        name="🤖 Status",
        value=(
            f"```\n"
            f"サーバー数: {len(client.guilds)}\n"
            f"ユーザー数: {len(client.users)}\n"
            f"```"
        ),
        inline=False,
    )

    # 稼働時間
    uptime_s = time.time() - client.start_time
    uptime_m = int(uptime_s / 60)
    uptime_h = int(uptime_m / 60)

    embed.add_field(
        name="💻 System",
        value=(
            f"```\n"
            f"メモリ使用量: {memory_usage:.2f}MB\n"
            f"CPU使用率: {cpu_usage:.2f}%\n"
            f"稼働時間: {uptime_s:.2f}s "
            f"({uptime_h}h {uptime_m}m {uptime_s}s)\n"
            "```"
        ),
        inline=False,
    )

    try:
        await message.edit(embed=embed, content=None)

    except discord.NotFound:
        await interaction.followup.send(embed=embed, content=None)

    except Exception:
        embed = discord.Embed(
            title="エラーが発生しました🥲",
            description="ping-Unknown-Exception",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(),
        )

        await interaction.followup.send(embed=embed, content=None, ephemeral=True)


@tree.command(
    name=locale_str("amidakuji"),
    description="Assign roles to users randomly.",
)
async def command_amidakuji(
    interaction: discord.Interaction,
):
    await interaction.response.defer(thinking=True, ephemeral=True)

    services = SimpleNamespace(db=interaction.client.db)
    context = CommandContext(
        interaction=interaction,
        state=AmidakujiState.COMMAND_EXECUTED,
        services=services,
    )

    flow = FlowController(context=context, services=services)
    services.flow = flow

    context.result = interaction

    view = ModeSelectionView(context=context)

    await interaction.followup.send(view=view, ephemeral=True)


@tree.command(
    name=locale_str("toggle_embed_mode"),
    description="Toggle the embed mode of the result of the command.",
)
async def command_toggle_embed_mode(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)

    db_manager = getattr(interaction.client, "db", None)
    if db_manager is None:
        raise RuntimeError("DB manager is not available")

    db_manager.toggle_embed_mode()
    current_mode = db_manager.get_embed_mode()

    embed = discord.Embed(
        title="埋め込みメッセージの表示形式を変更しました",
        description=f"現在の表示形式: {current_mode}",
        color=discord.Color.green(),
    )

    await interaction.followup.send(embed=embed, ephemeral=True)


@tree.command(
    name=locale_str("amidakuji_selection_mode"),
    description="抽選のアルゴリズムを切り替えます。",
)
@discord.app_commands.describe(mode="抽選モードを選択します。")
@discord.app_commands.choices(
    mode=[
        discord.app_commands.Choice(
            name="完全ランダム", value=SelectionMode.RANDOM.value
        ),
        discord.app_commands.Choice(
            name="偏り軽減", value=SelectionMode.BIAS_REDUCTION.value
        ),
    ]
)
async def command_set_selection_mode(
    interaction: discord.Interaction, mode: discord.app_commands.Choice[str]
):
    await interaction.response.defer(thinking=True, ephemeral=True)

    db_manager = getattr(interaction.client, "db", None)
    if db_manager is None:
        raise RuntimeError("DB manager is not available")

    try:
        selection_mode = SelectionMode(mode.value)
    except ValueError as error:
        raise RuntimeError("Invalid selection mode") from error

    db_manager.set_selection_mode(selection_mode)

    embed = discord.Embed(
        title="抽選モードを更新しました",
        description=f"現在のモード: {mode.name}",
        color=discord.Color.green(),
    )

    await interaction.followup.send(embed=embed, ephemeral=True)


@tree.command(
    name=locale_str("amidakuji_history"),
    description="最近の抽選履歴を表示します。",
)
@discord.app_commands.describe(
    limit="表示件数 (1-10)", template_title="絞り込みたいテンプレート名 (任意)"
)
async def command_amidakuji_history(
    interaction: discord.Interaction,
    limit: int = 5,
    template_title: str | None = None,
):
    await interaction.response.defer(thinking=True, ephemeral=True)

    db_manager = getattr(interaction.client, "db", None)
    if db_manager is None:
        raise RuntimeError("DB manager is not available")

    limit = max(1, min(10, limit))

    guild_id = interaction.guild_id or 0
    histories = db_manager.get_recent_history(
        guild_id=guild_id, template_title=template_title, limit=limit
    )

    if not histories:
        description = "抽選履歴が見つかりませんでした。"
        if template_title:
            description += f" (テンプレート: {template_title})"
        embed = discord.Embed(
            title="🎲 最近の抽選履歴",
            description=description,
            color=discord.Color.blue(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(
        title="🎲 最近の抽選履歴",
        description="最新の抽選結果を表示します。",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    for history in histories:
        try:
            selection_mode_label = {
                SelectionMode.RANDOM: "完全ランダム",
                SelectionMode.BIAS_REDUCTION: "偏り軽減",
            }[history.selection_mode]
        except KeyError:
            selection_mode_label = history.selection_mode.value

        timestamp_text = history.created_at.astimezone(
            datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            f"{entry.user_name} → {entry.choice}" for entry in history.entries
        ]
        field_value = "\n".join(lines) if lines else "記録がありません"
        if len(field_value) > 1024:
            field_value = field_value[:1010] + "\n..."

        field_name = (
            f"{history.template_title} ({timestamp_text}) [{selection_mode_label}]"
        )
        embed.add_field(name=field_name, value=field_value, inline=False)

    if template_title:
        embed.set_footer(text=f"テンプレート: {template_title}")

    await interaction.followup.send(embed=embed, ephemeral=True)


async def main():
    def load_client_token() -> str | None:
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            logging.warning(INFO + "`.env` file not found. Falling back to environment variables.")

        token_raw = os.getenv("CLIENT_TOKEN")
        if token_raw is None:
            logging.error("CLIENT_TOKEN not found in environment variables.")
            return None

        token = token_raw.strip()
        if not token:
            logging.error("CLIENT_TOKEN environment variable is empty after trimming whitespace.")
            return None

        if token != token_raw:
            logging.warning(INFO + "CLIENT_TOKEN contained leading/trailing whitespace; trimmed before use.")

        token_digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]
        token_length = len(token)
        logging.info(
            INFO
            + f"CLIENT_TOKEN detected (length={token_length}, sha256_prefix={token_digest})."
        )

        if token.count(".") != 2:
            logging.warning(
                INFO
                + "CLIENT_TOKEN does not match the expected Discord bot token format (two dots)."
            )

        return token

    TOKEN = load_client_token()
    if not TOKEN:
        logging.error("CLIENT_TOKEN environment variable not set.")
        return

    logging.info(INFO + "Client initialized. Setup hook will handle command sync.")

    async with client:
        logging.info(INFO + "Starting Discord client event loop.")
        await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
