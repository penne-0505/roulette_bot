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
        command_names = {
            "ja": {
                "ping": "ping",
                "amidakuji": "あみだくじ",
                # "toggle_embed_mode": "埋め込み形式切替", # なぜか、regexのバリデーションに引っかかる
            },
            "en-US": {
                "ping": "ping",
                "amidakuji": "amidakuji",
                # "toggle_embed_mode": "toggle embed mode",
            },
        }

        if (
            locale.value in command_names
            and string.message in command_names[locale.value]
        ):
            return command_names[locale.value][string.message]

        return None


# Emoji
EMOJI_LOL_TOP = 1345304239970324511
EMOJI_LOL_SUP = 1345304221477507114
EMOJI_LOL_MID = 1345304210669043752
EMOJI_LOL_JG = 1345304200741130240
EMOJI_LOL_BOT = 1345304183091368006


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
