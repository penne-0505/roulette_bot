from data_process import create_embeds_from_pairs
from models.model import Pair, PairList, ResultEmbedMode


class DummyAsset:
    def __init__(self, url: str | None):
        self.url = url


class DummyUser:
    def __init__(
        self,
        display_name: str,
        *,
        custom_avatar_url: str | None,
        fallback_avatar_url: str,
    ) -> None:
        self.display_name = display_name
        self.display_avatar = DummyAsset(custom_avatar_url or fallback_avatar_url)
        # ``avatar`` is intentionally set to None when a custom avatar is missing
        self.avatar = (
            DummyAsset(custom_avatar_url) if custom_avatar_url is not None else None
        )


def test_create_embeds_compact_mode_uses_display_avatar() -> None:
    user = DummyUser(
        "Custom Avatar User",
        custom_avatar_url="https://example.com/custom.png",
        fallback_avatar_url="https://example.com/default.png",
    )
    pair_list = PairList(pairs=[Pair(user=user, choice="Top Lane")])

    embeds = create_embeds_from_pairs(pair_list, mode=ResultEmbedMode.COMPACT)

    assert len(embeds) == 1
    embed = embeds[0]
    assert embed.author.icon_url == "https://example.com/custom.png"
    assert embed.author.name == " ┃ Top Lane"


def test_create_embeds_detailed_mode_handles_missing_custom_avatar() -> None:
    user = DummyUser(
        "Default Avatar User",
        custom_avatar_url=None,
        fallback_avatar_url="https://example.com/default.png",
    )
    pair_list = PairList(pairs=[Pair(user=user, choice="Jungle")])

    embeds = create_embeds_from_pairs(pair_list, mode=ResultEmbedMode.DETAILED)

    assert len(embeds) == 1
    embed = embeds[0]
    assert embed.title == "> Jungle"
    assert embed.author.icon_url == "https://example.com/default.png"
    assert embed.author.name == "Default Avatar User"

