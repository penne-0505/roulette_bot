import uuid

import discord
from colorama import Fore, Style


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class CommandsTranslator(discord.app_commands.Translator):
    _TRANSLATIONS: dict[str, dict[str, str]] = {
        # command names
        "ping": {
            "ja": "ping",
            "en-us": "ping",
        },
        "amidakuji": {
            "ja": "あみだくじ",
            "en-us": "amidakuji",
        },
        "amidakuji_template_create": {
            "ja": "テンプレート作成",
            "en-us": "template-create",
        },
        "amidakuji_template_manage": {
            "ja": "テンプレート管理",
            "en-us": "template-manage",
        },
        "amidakuji_template_share": {
            "ja": "テンプレート共有",
            "en-us": "template-share",
        },
        "toggle_embed_mode": {
            "ja": "表示モード切り替え",
            "en-us": "toggle-embed-mode",
        },
        "amidakuji_template_list": {
            "ja": "テンプレート一覧",
            "en-us": "template-list",
        },
        "amidakuji_selection_mode": {
            "ja": "抽選モード切り替え",
            "en-us": "selection-mode",
        },
        "amidakuji_history": {
            "ja": "抽選履歴",
            "en-us": "history",
        },
        # command descriptions
        "ping.description": {
            "ja": "Botの応答速度を確認します。🏓",
            "en-us": "Ping the bot. 🏓",
        },
        "amidakuji.description": {
            "ja": "指定した参加者に役割をランダムに割り当てます。",
            "en-us": "Assign roles to users randomly.",
        },
        "amidakuji_template_create.description": {
            "ja": "テンプレートを新規作成します。",
            "en-us": "Create a new template.",
        },
        "amidakuji_template_manage.description": {
            "ja": "テンプレートを編集または削除します。",
            "en-us": "Edit or delete your templates.",
        },
        "amidakuji_template_share.description": {
            "ja": "テンプレートの共有・公開設定を管理します。",
            "en-us": "Manage template sharing and publishing settings.",
        },
        "toggle_embed_mode.description": {
            "ja": "コマンド結果の埋め込み表示形式を切り替えます。",
            "en-us": "Toggle the embed mode of the command result.",
        },
        "amidakuji_template_list.description": {
            "ja": "利用可能なテンプレートを一覧表示します。",
            "en-us": "List available templates.",
        },
        "amidakuji_selection_mode.description": {
            "ja": "抽選のアルゴリズムを切り替えます。",
            "en-us": "Switch the selection algorithm.",
        },
        "amidakuji_history.description": {
            "ja": "最近の抽選履歴を表示します。",
            "en-us": "Show recent draw history.",
        },
        # option descriptions
        "amidakuji_history.limit": {
            "ja": "表示件数 (1-10)",
            "en-us": "Number of entries to show (1-10)",
        },
        "amidakuji_history.template_title": {
            "ja": "絞り込みたいテンプレート名 (任意)",
            "en-us": "Template name filter (optional)",
        },
    }

    @staticmethod
    def _resolve_locale(locale: discord.Locale) -> list[str]:
        value = locale.value
        if not value:
            return []

        normalized = value.lower()
        locales = [normalized]
        if "-" in normalized:
            base = normalized.split("-", 1)[0]
            if base not in locales:
                locales.append(base)
        return locales

    async def translate(
        self,
        string: discord.app_commands.locale_str,
        locale: discord.Locale,
        context: discord.app_commands.TranslationContext,
    ) -> str | None:
        message = string.message
        if not message:
            return None

        translations = self._TRANSLATIONS.get(message)
        if not translations:
            return None

        for candidate in self._resolve_locale(locale):
            if candidate in translations:
                return translations[candidate]

        value = locale.value
        if value and value.lower().startswith("en"):
            fallback = translations.get("en-us") or translations.get("en")
            if fallback is not None:
                return fallback

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


def generate_template_id() -> str:
    """Return a unique identifier for template documents."""

    return uuid.uuid4().hex


if __name__ == "__main__":
    pass
