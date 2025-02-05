import random

import discord


def create_pair_from_list(
    users: list[discord.User], groupes: list[str]
) -> list[dict[discord.User, str]]:
    if not users or not groupes:
        raise ValueError("users and groupes must not be empty")

    pairs = []
    pairs_amount = min(len(users), len(groupes))

    shuffled_users = users.copy()
    shuffled_groupes = groupes.copy()
    random.shuffle(shuffled_users)
    random.shuffle(shuffled_groupes)

    pairs = [{shuffled_users[i]: shuffled_groupes[i]} for i in range(pairs_amount)]

    return pairs
