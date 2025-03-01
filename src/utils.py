import discord
from colorama import Fore, Style


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class CommandsTranslator(discord.app_commands.Translator):
    async def translate(
        self,
        string: discord.app_commands.locale_str,
        locale: discord.Locale,
        context: discord.app_commands.TranslationContext,
    ) -> str | None:
        translations = {
            "en-US": {
                "ping": "ping",
                "amidakuji": "amidakuji",
                "toggle_embed_mode": "toggle_embed_mode",
                # 以下はコマンドの説明文
                "Ping the bot. 🏓": "Ping the bot. 🏓",
                "Assign roles to users randomly.": "Assign roles to users randomly.",
                "Toggle the embed mode of the result of the command.": "Toggle the embed mode of the result of the command.",
            },
            "ja": {
                "ping": "ping",
                "amidakuji": "あみだくじ",
                "toggle_embed_mode": "埋め込み表示切替",
                # 以下はコマンドの説明文
                "Ping the bot. 🏓": "いろいろな情報を表示します🏓",
                "Assign roles to users randomly.": "ユーザーに役割をランダムに割り当てます。(いわゆるあみだくじを行います)",
                "Toggle the embed mode of the result of the command.": "コマンドの結果の表示モードを切り替えます。",
            },
        }

        if locale.value in translations and string in translations[locale.value]:
            return translations[locale.value][string]

        return None


# logging constants
INFO = f"{Fore.BLUE}[INFO]{Style.RESET_ALL}: "
ERROR = f"{Fore.RED}[ERROR]{Style.RESET_ALL}: "
WARN = f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL}: "
DEBUG = f"{Fore.MAGENTA}[DEBUG]{Style.RESET_ALL}: "
SUCCESS = f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL}: "
FORMAT = str(f"{Style.BRIGHT}%(asctime)s{Style.RESET_ALL} - %(message)s")
DATEFORMAT = str("%Y-%m-%d %H:%M:%S")


def blue(text: str) -> str:
    return f"{Fore.BLUE}{text}{Style.RESET_ALL}"


def red(text: str) -> str:
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def yellow(text: str) -> str:
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"


def magenta(text: str) -> str:
    return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"


def green(text: str) -> str:
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def cyan(text: str) -> str:
    return f"{Fore.CYAN}{text}{Style.RESET_ALL}"


def bold(text: str) -> str:
    return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"


if __name__ == "__main__":
    pass
