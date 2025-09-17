from types import SimpleNamespace

from components.select import remove_bots


def test_remove_bots_filters_out_bot_accounts():
    human = SimpleNamespace(name="human", bot=False)
    bot = SimpleNamespace(name="bot", bot=True)
    unknown = SimpleNamespace(name="unknown")

    filtered = remove_bots([human, bot, unknown])

    assert filtered == [human, unknown]
