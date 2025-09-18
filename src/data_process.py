import random

import discord

from models.model import Pair, PairList, ResultEmbedMode


def create_pair_from_list(users: list[discord.User], groupes: list[str]) -> PairList:
    if not users or not groupes:
        raise ValueError("ユーザーまたはグループが空です")

    pairs = []
    pairs_amount = min(len(users), len(groupes))

    shuffled_users = users.copy()
    shuffled_groupes = groupes.copy()
    random.shuffle(shuffled_users)
    random.shuffle(shuffled_groupes)

    for i in range(pairs_amount):
        pairs.append(Pair(user=shuffled_users[i], choice=shuffled_groupes[i]))

    return PairList(pairs=pairs)


# TODO: 将来的に、utils.pyで定義されているlolの絵文字を使って、レーンごとに絵文字も併せて表示するように変更する
def _normalize_mode(mode: ResultEmbedMode | str) -> str:
    if isinstance(mode, ResultEmbedMode):
        return mode.value
    return str(mode).lower()


def _build_compact_embed(pair: Pair) -> discord.Embed:
    embed = discord.Embed()
    avatar_asset = getattr(pair.user, "display_avatar", None)
    embed.set_author(
        icon_url=getattr(avatar_asset, "url", None),
        name=f" ┃ {pair.choice}",
    )
    return embed


def _build_detailed_embed(pair: Pair) -> discord.Embed:
    embed = discord.Embed()
    embed.title = f"> {pair.choice}"
    avatar_asset = getattr(pair.user, "display_avatar", None)
    embed.set_author(
        icon_url=getattr(avatar_asset, "url", None),
        name=pair.user.display_name,
    )
    return embed


def create_embeds_from_pairs(
    pairs: PairList, mode: ResultEmbedMode = ResultEmbedMode.COMPACT
) -> list[discord.Embed]:
    pair_list = pairs.pairs
    normalized_mode = _normalize_mode(mode)
    builder_map = {
        ResultEmbedMode.COMPACT.value: _build_compact_embed,
        ResultEmbedMode.DETAILED.value: _build_detailed_embed,
    }

    builder = builder_map.get(normalized_mode)
    if builder is None:
        return []

    return [builder(pair) for pair in pair_list]


if __name__ == "__main__":
    pass
