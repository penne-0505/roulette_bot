from enum import Enum
from typing import Any, Dict, List, Type, TypeAlias, Union, get_origin

import discord

from domain import PairList, Template
from models.state_model import AmidakujiState


class AmidakujiStateTypes(Enum):
    EXPECTED_TYPES: TypeAlias = Union[
        discord.Interaction,
        str,
        int,
        Template,
        List[discord.User],
        PairList,
    ]

    COMMAND_EXECUTED: TypeAlias = discord.Interaction

    MODE_USE_EXISTING: TypeAlias = discord.Interaction
    MODE_CREATE_NEW: TypeAlias = discord.Interaction
    MODE_USE_HISTORY: TypeAlias = discord.Interaction
    MODE_DELETE_TEMPLATE: TypeAlias = discord.Interaction
    MODE_USE_SHARED: TypeAlias = discord.Interaction
    MODE_USE_PUBLIC: TypeAlias = discord.Interaction

    TEMPLATE_TITLE_ENTERED: TypeAlias = str
    TEMPLATE_CREATED: TypeAlias = Template
    OPTION_NAME_ENTERED: TypeAlias = List[str]
    OPTION_MANAGE_SELECTED: TypeAlias = int
    OPTION_DELETED: TypeAlias = discord.Interaction
    OPTION_MOVED_UP: TypeAlias = discord.Interaction
    OPTION_MOVED_DOWN: TypeAlias = discord.Interaction
    ENTER_OPTION_BUTTON_CLICKED: TypeAlias = discord.Interaction
    NEED_MORE_OPTIONS: TypeAlias = discord.Interaction

    TEMPLATE_DETERMINED: TypeAlias = Template

    TEMPLATE_DELETED: TypeAlias = str
    SHARED_TEMPLATE_SELECTED: TypeAlias = Template
    SHARED_TEMPLATE_COPY_REQUESTED: TypeAlias = Template

    MEMBER_SELECTED: TypeAlias = List[discord.User]

    CANCELLED: TypeAlias = discord.Interaction


class TypeRegistry:
    """キーに対応する型情報を管理するレジストリ"""

    # 型情報のマッピング
    _type_map: Dict[AmidakujiState, Type] = {
        AmidakujiState.COMMAND_EXECUTED: discord.Interaction,
        AmidakujiState.MODE_USE_EXISTING: discord.Interaction,
        AmidakujiState.MODE_CREATE_NEW: discord.Interaction,
        AmidakujiState.MODE_USE_HISTORY: discord.Interaction,
        AmidakujiState.MODE_DELETE_TEMPLATE: discord.Interaction,
        AmidakujiState.MODE_USE_SHARED: discord.Interaction,
        AmidakujiState.MODE_USE_PUBLIC: discord.Interaction,
        AmidakujiState.TEMPLATE_TITLE_ENTERED: str,
        AmidakujiState.TEMPLATE_CREATED: Template,
        AmidakujiState.OPTION_NAME_ENTERED: list[str],
        AmidakujiState.OPTION_MANAGE_SELECTED: int,
        AmidakujiState.OPTION_DELETED: discord.Interaction,
        AmidakujiState.OPTION_MOVED_UP: discord.Interaction,
        AmidakujiState.OPTION_MOVED_DOWN: discord.Interaction,
        AmidakujiState.ENTER_OPTION_BUTTON_CLICKED: discord.Interaction,
        AmidakujiState.NEED_MORE_OPTIONS: discord.Interaction,
        AmidakujiState.TEMPLATE_DETERMINED: Template,
        AmidakujiState.TEMPLATE_DELETED: str,
        AmidakujiState.SHARED_TEMPLATE_SELECTED: Template,
        AmidakujiState.SHARED_TEMPLATE_COPY_REQUESTED: Template,
        AmidakujiState.MEMBER_SELECTED: list[discord.User],
        AmidakujiState.CANCELLED: discord.Interaction,
    }

    @classmethod
    def get_type(cls, key: AmidakujiState) -> Type:
        """キーに対応する型情報を取得する"""
        if key not in cls._type_map:
            raise ValueError(f"Type for key '{key}' not registered")
        return cls._type_map[key]

    @classmethod
    def validate(cls, key: AmidakujiState, value: Any) -> bool:
        """値が指定されたキーの型に合致するか検証する"""
        type_ = cls.get_type(key)

        # 単純な型の場合
        if type_ in [str, int, float, bool]:
            return isinstance(value, type_)

        # リストの場合
        if get_origin(type_) is list:
            if not isinstance(value, list):
                return False
            # ここでリストの要素型をさらに検証することも可能

        # クラスの場合
        if isinstance(type_, type):
            return isinstance(value, type_)

        # 複雑な型の場合、簡易的に型名で確認
        return str(type(value).__name__) == str(type_.__name__)


if __name__ == "__main__":
    pass
