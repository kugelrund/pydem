import copy

import format
from messages import ItemFlags


def nextmap(stats: format.ClientStats) -> format.ClientStats:
    new_stats = copy.deepcopy(stats)
    new_stats.items = stats.items & ~(stats.items & (
        ItemFlags.SUPERHEALTH|ItemFlags.KEY1|ItemFlags.KEY2|
        ItemFlags.INVISIBILITY|ItemFlags.INVULNERABILITY|ItemFlags.SUIT|
        ItemFlags.QUAD))
    new_stats.health = min(max(stats.health, 50), 100)
    new_stats.shells = max(stats.shells, 25)
    return new_stats
