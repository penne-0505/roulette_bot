from dataclasses import dataclass

import discord
from colorama import Fore, Style


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class CommandContext:
    interaction: discord.Interaction
    result: dict[int, ]


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
