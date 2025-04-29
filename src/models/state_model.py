from enum import Enum, auto


class AmidakujiState(Enum):
    COMMAND_EXECUTED = auto()

    MODE_USE_EXISTING = auto()
    MODE_CREATE_NEW = auto()
    MODE_USE_HISTORY = auto()

    TEMPLATE_TITLE_ENTERED = auto()
    ENTER_OPTION_BUTTON_CLICKED = auto()
    OPTION_NAME_ENTERED = auto()
    NEED_MORE_OPTIONS = auto()
    TEMPLATE_CREATED = auto()

    TEMPLATE_DETERMINED = auto()

    MEMBER_SELECTED = auto()

    CANCELLED = auto()
