from types import SimpleNamespace

import data_process
from data_process import create_embeds_from_pairs, create_pair_from_list
from domain import Pair, PairList, ResultEmbedMode, SelectionMode


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


def test_create_pair_from_list_bias_reduction_respects_weights(monkeypatch) -> None:
    user_a = SimpleNamespace(id=1, display_name="UserA")
    user_b = SimpleNamespace(id=2, display_name="UserB")

    groupes = ["Top", "Jungle"]

    def fake_shuffle(sequence):
        # Keep order stable for deterministic testing
        return None

    def fake_choices(population, weights, k):
        assert k == 1
        if weights[0] == 0.0:
            return [population[1]]
        return [population[0]]

    monkeypatch.setattr(data_process.random, "shuffle", fake_shuffle)
    monkeypatch.setattr(data_process.random, "choices", fake_choices)

    pairs = create_pair_from_list(
        [user_a, user_b],
        groupes,
        selection_mode=SelectionMode.BIAS_REDUCTION,
        weights={
            user_a.id: {"Top": 0.0, "Jungle": 1.0},
            user_b.id: {"Top": 1.0, "Jungle": 1.0},
        },
    )

    assert len(pairs.pairs) == 2
    assert pairs.pairs[0].user is user_b
    assert pairs.pairs[0].choice == "Top"
    assert pairs.pairs[1].user is user_a
    assert pairs.pairs[1].choice == "Jungle"

