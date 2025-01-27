import datetime
import logging
import os
import time

import discord
import psutil
from discord.app_commands import locale_str
from dotenv import load_dotenv

from roulette_ds_bot.src.utils import (
    DATEFORMAT,
    DEBUG,
    ERROR,
    FORMAT,
    INFO,
    SUCCESS,
    WARN,
    blue,
    bold,
    cyan,
    green,
    magenta,
    red,
    yellow,
)

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
        # コマンドの同期
        await self.sync_commands()

        # 以下ログ
        logging.info(
            INFO + f"Logged in as {green(self.user.name)} ({blue(self.user.id)})"
        )
        logging.info(INFO + f"Connected to {green(len(self.guilds))} guilds")
        logging.info(INFO + f"Launch time: {green(time.time() - self.start_time)}s")
        logging.info(INFO + bold("Bot is ready."))

    async def setup_hook(self) -> None:
        # コマンドの翻訳の呼び出しはここで行う
        return

    async def sync_commands(self) -> None:
        await tree.sync()

    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command | discord.app_commands.ContextMenu,
    ):
        # 装飾してログを出力
        exec_guild = yellow(interaction.guild) if interaction.guild else "DM"
        exec_channel = magenta(interaction.channel) if interaction.channel else "(DM)"
        exec_user = interaction.user
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


@tree.command(name=locale_str("ping"), description=locale_str("Ping the bot."))
async def command_ping(interaction: discord.Interaction):
    # 返信の遅延
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
    uptime_ms = time.time() - client.start_time
    uptime_s = int(uptime_ms / 1000)
    uptime_m = int(uptime_s / 60)
    uptime_h = int(uptime_m / 60)

    embed.add_field(
        name="💻 System",
        value=(
            f"```\n"
            f"メモリ使用量: {memory_usage:.2f}MB\n"
            f"CPU使用率: {cpu_usage:.2f}%\n"
            f"稼働時間: {uptime_ms:.2f}ms "
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
        await interaction.followup.send("エラーが発生しました🥲", ephemeral=True)
        raise


@tree.command(
    name=locale_str("amidakuji"),
    description=locale_str("assign roles to users randomly"),
)
async def command_amidakuji(
    interaction: discord.Interaction,
):
    await interaction.response.defer(thinking=True)

    avatar = interaction.user.display_avatar.url
    embed = discord.Embed()
    embed.set_author(name=interaction.user.display_name, icon_url=avatar)

    await interaction.followup.send(embeds=[embed for _ in range(5)])


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("CLIENT_TOKEN")
    client.run(TOKEN)
