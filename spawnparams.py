import copy

import format
from messages import ItemFlags
import stats


def nextmap(stats: format.ClientStats) -> format.ClientStats:
    new_stats = copy.deepcopy(stats)
    new_stats.items = stats.items & ~(stats.items & (
        ItemFlags.SUPERHEALTH|ItemFlags.KEY1|ItemFlags.KEY2|
        ItemFlags.INVISIBILITY|ItemFlags.INVULNERABILITY|ItemFlags.SUIT|
        ItemFlags.QUAD))
    new_stats.health = min(max(stats.health, 50), 100)
    new_stats.shells = max(stats.shells, 25)
    return new_stats


def get_activeweapon_spawnparam(activeweapon_stats):
    # qdqstats progs handle the spawn param for the active weapon in a
    # special way. We mirror that in this function to be able to figure
    # out the next spawn params.
    if activeweapon_stats == ItemFlags.AXE:
        return 0.0
    elif activeweapon_stats == ItemFlags.SHOTGUN:
        return 1.0
    elif activeweapon_stats == ItemFlags.SUPER_SHOTGUN:
        return 2.0
    elif activeweapon_stats == ItemFlags.NAILGUN:
        return 3.0
    elif activeweapon_stats == ItemFlags.SUPER_NAILGUN:
        return 4.0
    elif activeweapon_stats == ItemFlags.GRENADE_LAUNCHER:
        return 5.0
    elif activeweapon_stats == ItemFlags.ROCKET_LAUNCHER:
        return 6.0
    elif activeweapon_stats == ItemFlags.LIGHTNING:
        return 7.0
    else:
        raise ValueError("Unknown active weapon")


def write_cfg(cfg_path, demo_per_player):
    with open(cfg_path, 'w') as f:
        for i, demo in enumerate(demo_per_player):
            next_stats = nextmap(demo.get_final_client_stats())
            f.write(f"setspawnparam 0 {float(next_stats.items)} {i}\n")
            f.write(f"setspawnparam 1 {float(next_stats.health)} {i}\n")
            f.write(f"setspawnparam 2 {float(next_stats.armor)} {i}\n")
            f.write(f"setspawnparam 3 {float(next_stats.shells)} {i}\n")
            f.write(f"setspawnparam 4 {float(next_stats.nails)} {i}\n")
            f.write(f"setspawnparam 5 {float(next_stats.rockets)} {i}\n")
            f.write(f"setspawnparam 6 {float(next_stats.cells)} {i}\n")
            activeweapon_spawnparam = get_activeweapon_spawnparam(
                next_stats.activeweapon)
            f.write(f"setspawnparam 7 {activeweapon_spawnparam} {i}\n")
            armortype = stats.get_damage_reduction(next_stats.items)
            f.write(f"setspawnparam 8 {armortype} {i}\n")
