import random
from collections import defaultdict

import discord

from domain import Pair, PairList, ResultEmbedMode, SelectionMode
from domain.services.selection_mode_service import coerce_selection_mode


def _normalize_selection_mode(mode: SelectionMode | str) -> str:
    return coerce_selection_mode(mode).value


def _build_weight_matrix(
    users: list[discord.User],
    groupes: list[str],
    weights: dict[int, dict[str, float]] | None,
) -> dict[int, dict[str, float]]:
    if weights is None:
        return {user.id: {group: 1.0 for group in groupes} for user in users}

    matrix: dict[int, dict[str, float]] = defaultdict(dict)
    for user in users:
        user_weights = weights.get(user.id, {})
        matrix[user.id] = {
            group: max(float(user_weights.get(group, 1.0)), 0.0) for group in groupes
        }
    return matrix


def create_pair_from_list(
    users: list[discord.User],
    groupes: list[str],
    *,
    selection_mode: SelectionMode | str = SelectionMode.RANDOM,
    weights: dict[int, dict[str, float]] | None = None,
) -> PairList:
    if not users or not groupes:
        raise ValueError("ユーザーまたはグループが空です")

    pairs = []
    pairs_amount = min(len(users), len(groupes))

    shuffled_groupes = groupes.copy()
    random.shuffle(shuffled_groupes)

    normalized_mode = _normalize_selection_mode(selection_mode)

    if normalized_mode != SelectionMode.BIAS_REDUCTION.value:
        shuffled_users = users.copy()
        random.shuffle(shuffled_users)

        for i in range(pairs_amount):
            pairs.append(Pair(user=shuffled_users[i], choice=shuffled_groupes[i]))
        return PairList(pairs=pairs)

    weight_matrix = _build_weight_matrix(users, shuffled_groupes, weights)

    available_users = users.copy()
    for group in shuffled_groupes[:pairs_amount]:
        user_weights = [weight_matrix[user.id][group] for user in available_users]
        total_weight = sum(user_weights)
        if total_weight <= 0:
            selected_user = random.choice(available_users)
        else:
            selected_user = random.choices(available_users, weights=user_weights, k=1)[0]

        pairs.append(Pair(user=selected_user, choice=group))
        available_users.remove(selected_user)

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
