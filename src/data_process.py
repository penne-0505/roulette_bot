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
def create_embeds_from_pairs(
    pairs: PairList, mode: ResultEmbedMode = ResultEmbedMode.COMPACT
) -> list[discord.Embed]:
    embeds: list[discord.Embed] = []

    pair_list = pairs.pairs
    if isinstance(mode, ResultEmbedMode):
        normalized_mode = mode.value
    else:
        normalized_mode = str(mode).lower()

    if normalized_mode == ResultEmbedMode.COMPACT.value:
        for pair in pair_list:
            embed = discord.Embed()
            avatar_asset = getattr(pair.user, "display_avatar", None)
            embed.set_author(
                icon_url=getattr(avatar_asset, "url", None),
                name=f" ┃ {pair.choice}",
            )
            embeds.append(embed)
        return embeds

    elif normalized_mode == ResultEmbedMode.DETAILED.value:
        for pair in pair_list:
            embed = discord.Embed()
            embed.title = f"> {pair.choice}"
            avatar_asset = getattr(pair.user, "display_avatar", None)
            embed.set_author(
                icon_url=getattr(avatar_asset, "url", None),
                name=pair.user.display_name,
            )
            embeds.append(embed)
        return embeds

    return embeds


if __name__ == "__main__":
    pass
