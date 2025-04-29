import datetime
import logging
import os
import time

import discord
import psutil
from discord.app_commands import locale_str

from db_manager import db
from models.context_model import CommandContext
from models.state_model import AmidakujiState
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


class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.start_time = time.time()

    async def on_ready(self):
        await self.sync_commands()

        db._init_default_templates()

        logging.info(
            INFO + f"Logged in as {green(self.user.name)} ({blue(self.user.id)})"
        )
        logging.info(INFO + f"Connected to {green(len(self.guilds))} guilds")
        logging.info(INFO + f"Launch time: {green(time.time() - self.start_time)}s")
        logging.info(INFO + bold("Bot is ready."))

    async def setup_hook(self) -> None:
        await tree.set_translator(CommandsTranslator())

    async def sync_commands(self) -> None:
        await tree.sync()

    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command | discord.app_commands.ContextMenu,
    ):
        exec_user = interaction.user
        user_id = exec_user.id
        if not db.user_is_exist(user_id):
            db.init_user(user_id=user_id, name=exec_user.name)

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
client.sync_commands()


@tree.command(name=locale_str("ping"), description="Ping the bot. 🏓")
async def command_ping(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    ws_latency = round(client.latency * 1000)

    start_time = time.perf_counter()
    message = await interaction.followup.send("測定中...")
    end_time = time.perf_counter()
    api_latency = round((end_time - start_time) * 1000)

    process = psutil.Process()
    memory_usage = process.memory_info().rss / 1024 / 1024
    cpu_usage = process.cpu_percent()

    embed = discord.Embed(
        title="🏓 Pong!", color=discord.Color.green(), timestamp=datetime.datetime.now()
    )

    embed.add_field(
        name="📡 Connection",
        value=(f"```\nWebsocket: {ws_latency}ms\nAPI: {api_latency}ms\n```"),
        inline=False,
    )

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

    context = CommandContext(
        interaction=interaction,
        state=AmidakujiState.COMMAND_EXECUTED,
    )

    context.result = interaction

    view = ModeSelectionView(context=context)

    await interaction.followup.send(view=view, ephemeral=True)


@tree.command(
    name=locale_str("toggle_embed_mode"),
    description="Toggle the embed mode of the result of the command.",
)
async def command_toggle_embed_mode(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)

    db.toggle_embed_mode()
    current_mode = db.get_embed_mode()

    embed = discord.Embed(
        title="埋め込みメッセージの表示形式を変更しました",
        description=f"現在の表示形式: {current_mode}",
        color=discord.Color.green(),
    )

    await interaction.followup.send(embed=embed, ephemeral=True)


if __name__ == "__main__":
    TOKEN = os.getenv("CLIENT_TOKEN")
    client.run(TOKEN)
