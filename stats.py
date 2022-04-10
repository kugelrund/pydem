import copy
import dataclasses
import enum
import math

import collision
import format
import messages
from messages import ItemFlags


class CollectSound(enum.Enum):
    HP15 = b'items/r_item1.wav'
    HP25 = b'items/health1.wav'
    HP100 = b'items/r_item2.wav'
    ARMOR = b'items/armor1.wav'
    AMMO = b'weapons/lock4.wav'
    WEAPON = b'weapons/pkup.wav'

COLLECT_SOUNDS = [x.value for x in CollectSound]


@dataclasses.dataclass
class Health:
    value: int

@dataclasses.dataclass
class Shells:
    value: int

@dataclasses.dataclass
class Nails:
    value: int

@dataclasses.dataclass
class Rockets:
    value: int

@dataclasses.dataclass
class Cells:
    value: int

@dataclasses.dataclass
class Armor:
    value: int

@dataclasses.dataclass
class Item:
    value: ItemFlags


MIN_HEALTH = 1
MAX_HEALTH = 100
MAX_MEGAHEALTH = 250
MIN_SHELLS = 0
MAX_SHELLS = 100
MIN_NAILS = 0
MAX_NAILS = 200
MIN_ROCKETS = 0
MAX_ROCKETS = 100
MIN_CELLS = 0
MAX_CELLS = 100

def get_damage_reduction(items: ItemFlags) -> float:
    damage_reduction = 0.0
    if items & ItemFlags.ARMOR1:
        damage_reduction = 0.3
    elif items & ItemFlags.ARMOR2:
        damage_reduction = 0.6
    elif items & ItemFlags.ARMOR3:
        damage_reduction = 0.8
    return damage_reduction

class CollectableItemHealth15:
    gives = [Health(15)]
    collect_sound = CollectSound.HP15
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 15 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.health < MAX_HEALTH

class CollectableItemHealth25:
    gives = [Health(25)]
    collect_sound = CollectSound.HP25
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 25 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.health < MAX_HEALTH

class CollectableItemHealth100:
    gives = [Item(ItemFlags.SUPERHEALTH), Health(100)]
    collect_sound = CollectSound.HP100
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 100 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return True

class CollectableItemShells20:
    gives = [Shells(20)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the shells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.shells < MAX_SHELLS

class CollectableItemShells40:
    gives = [Shells(40)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the shells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.shells < MAX_SHELLS

class CollectableItemNails25:
    gives = [Nails(25)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the nails\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.nails < MAX_NAILS

class CollectableItemNails50:
    gives = [Nails(50)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the nails\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.nails < MAX_NAILS

class CollectableItemRockets5:
    gives = [Rockets(5)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the rockets\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.rockets < MAX_ROCKETS

class CollectableItemRockets10:
    gives = [Rockets(10)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the rockets\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.rockets < MAX_ROCKETS

class CollectableItemCells6:
    gives = [Cells(6)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the cells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.cells < MAX_CELLS

class CollectableItemCells12:
    gives = [Cells(12)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the cells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.cells < MAX_CELLS

class CollectableItemGreenArmor:
    armor_value = 100
    gives = [Item(ItemFlags.ARMOR1), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR1) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)

class CollectableItemYellowArmor:
    armor_value = 150
    gives = [Item(ItemFlags.ARMOR2), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR2) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)

class CollectableItemRedArmor:
    armor_value = 200
    gives = [Item(ItemFlags.ARMOR3), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR3) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)

class CollectableItemSuperShotgun:
    gives = [Item(ItemFlags.SUPER_SHOTGUN), Shells(5)]
    collect_sound = CollectSound.WEAPON
    print_text = b"You got the Double-barrelled Shotgun\n"
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.SUPER_SHOTGUN)

class CollectableItemNailgun:
    gives = [Item(ItemFlags.NAILGUN), Nails(30)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Nailgun\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.NAILGUN)

class CollectableItemSuperNailgun:
    gives = [Item(ItemFlags.SUPER_NAILGUN), Nails(30)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Super Nailgun\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.SUPER_NAILGUN)

class CollectableItemGrenadeLauncher:
    gives = [Item(ItemFlags.GRENADE_LAUNCHER), Rockets(5)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Grenade Launcher\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.GRENADE_LAUNCHER)

class CollectableItemRocketLauncher:
    gives = [Item(ItemFlags.ROCKET_LAUNCHER), Rockets(5)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Rocket Launcher\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.ROCKET_LAUNCHER)

class CollectableItemLightningGun:
    gives = [Item(ItemFlags.LIGHTNING), Cells(15)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Thunderbolt\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.LIGHTNING)

@dataclasses.dataclass
class CollectableItemBackpack:
    gives = [Shells(math.inf), Nails(math.inf), Rockets(math.inf), Cells(math.inf)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]

    @staticmethod
    def will_collect(stats, is_coop):
        return True


def get_pickup_health(item_type):
    return sum([x.value for x in item_type.gives if isinstance(x, Health)])

def get_pickup_shells(item_type):
    return sum([x.value for x in item_type.gives if isinstance(x, Shells)])

def get_pickup_nails(item_type):
    return sum([x.value for x in item_type.gives if isinstance(x, Nails)])

def get_pickup_rockets(item_type):
    return sum([x.value for x in item_type.gives if isinstance(x, Rockets)])

def get_pickup_cells(item_type):
    return sum([x.value for x in item_type.gives if isinstance(x, Cells)])

def get_pickup_armor(item_type):
    return sum([x.value for x in item_type.gives if isinstance(x, Armor)])

def get_pickup_items(item_type):
    item_flags = 0
    for flags in [x.value for x in item_type.gives if isinstance(x, Item)]:
        item_flags |= flags
    return item_flags


COLLECTABLE_MODELS_MAP = {
    b'maps/b_bh10.bsp': CollectableItemHealth15,
    b'maps/b_bh25.bsp': CollectableItemHealth25,
    b'maps/b_bh100.bsp': CollectableItemHealth100,
    b'maps/b_shell0.bsp': CollectableItemShells20,
    b'maps/b_shell1.bsp': CollectableItemShells40,
    b'maps/b_nail0.bsp': CollectableItemNails25,
    b'maps/b_nail1.bsp': CollectableItemNails50,
    b'maps/b_rock0.bsp': CollectableItemRockets5,
    b'maps/b_rock1.bsp': CollectableItemRockets10,
    b'maps/b_batt0.bsp': CollectableItemCells6,
    b'maps/b_batt1.bsp': CollectableItemCells12,
    b'progs/armor.mdl': None,  # depends on skin, so has to be handled in special way
    b'progs/g_shot.mdl': CollectableItemSuperShotgun,
    b'progs/g_nail.mdl': CollectableItemNailgun,
    b'progs/g_nail2.mdl': CollectableItemSuperNailgun,
    b'progs/g_rock.mdl': CollectableItemGrenadeLauncher,
    b'progs/g_rock2.mdl': CollectableItemRocketLauncher,
    b'progs/g_light.mdl': CollectableItemLightningGun,
}

@dataclasses.dataclass
class SoundCollectEvent:
    block_index: int
    sound_num: int
    origin: list[float]
    sound: CollectSound

@dataclasses.dataclass
class CollectableItem:
    entity_num: int
    origin: list[float]
    type: None
    sound_event: SoundCollectEvent
    frame_collected: int

    def will_collect(self, stats, is_coop):
        return self.type.will_collect(stats, is_coop)

    def get_pickup_health(self):
        return get_pickup_health(self.type)
    def get_pickup_shells(self):
        return get_pickup_shells(self.type)
    def get_pickup_nails(self):
        return get_pickup_nails(self.type)
    def get_pickup_rockets(self):
        return get_pickup_rockets(self.type)
    def get_pickup_cells(self):
        return get_pickup_cells(self.type)
    def get_pickup_armor(self):
        return get_pickup_armor(self.type)
    def get_pickup_items(self):
        return get_pickup_items(self.type)

    def bounds(self, frame: int):
        return collision.bounds_item(self.origin[frame], self.type.mins, self.type.maxs)


def get_precaches(demo):
    server_info_message = [m for b in demo.blocks for m in b.messages
                           if isinstance(m, messages.ServerInfoMessage)]
    assert len(server_info_message) == 1
    return (server_info_message[0].models_precache,
            server_info_message[0].sounds_precache)

def get_collectable_items(demo, models_precache):
    static_collectable_items = dict()
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.SpawnBaselineMessage):
                model_name = models_precache[m.modelindex]
                if model_name in COLLECTABLE_MODELS_MAP.keys():
                    assert m.entity_num not in static_collectable_items
                    if model_name == b'progs/armor.mdl':
                        if m.skin == 0:
                            item_type = CollectableItemGreenArmor
                        elif m.skin == 1:
                            item_type = CollectableItemYellowArmor
                        else:
                            assert m.skin == 2
                            item_type = CollectableItemRedArmor
                    else:
                        item_type = COLLECTABLE_MODELS_MAP[model_name]
                    static_collectable_items[m.entity_num] = CollectableItem(
                        m.entity_num, [list(m.origin) for _ in range(len(demo.blocks))], item_type, None, math.inf)
            elif isinstance(m, messages.EntityUpdateMessage):
                if m.num in static_collectable_items:
                    if m.flags & messages.UpdateFlags.ORIGIN1:
                        static_collectable_items[m.num].origin[i][0] = m.origin[0]
                    if m.flags & messages.UpdateFlags.ORIGIN2:
                        static_collectable_items[m.num].origin[i][1] = m.origin[1]
                    if m.flags & messages.UpdateFlags.ORIGIN3:
                        static_collectable_items[m.num].origin[i][2] = m.origin[2]

    return static_collectable_items

def get_viewent_num(demo):
    set_view_messages = [m for b in demo.blocks for m in b.messages
                         if isinstance(m, messages.SetViewMessage)]
    assert len(set_view_messages) >= 1
    viewent_num = set_view_messages[0].viewentity_id
    assert all([m.viewentity_id == viewent_num for m in set_view_messages])
    return viewent_num

def get_client_positions(demo, client_num):
    client_positions = []
    for block in demo.blocks:
        client_messages = [m for m in block.messages
                           if isinstance(m, messages.EntityUpdateMessage) and m.num == client_num]
        if client_messages:
            assert len(client_messages) == 1
            client_positions.append(client_messages[0].origin)
        else:
            client_positions.append([math.inf]*3)
    return client_positions

def find_closest_item_to_client(client_origin, items, block_index):
    closest_distance = math.inf
    closest_item = None
    for item in items:
        distance = collision.distance(collision.bounds_player(client_origin),
                                      item.bounds(frame=block_index))
        if distance < closest_distance:
            closest_item = item
            closest_distance = distance
    return closest_item, closest_distance

def get_changeable_collections(demo):
    models_precache, sounds_precache = get_precaches(demo)
    static_collectable_items = get_collectable_items(demo, models_precache)
    items_by_frame = [[] for _ in range(len(demo.blocks))]
    sound_pickup_events = []
    viewent_num = get_viewent_num(demo)
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.EntityUpdateMessage):
                if m.num in static_collectable_items:
                    items_by_frame[i].append(static_collectable_items[m.num])
            elif isinstance(m, messages.SoundMessage):
                sound_name = sounds_precache[m.sound_num]
                if m.ent == viewent_num and sound_name in COLLECT_SOUNDS:
                    sound_pickup_events.append(SoundCollectEvent(
                        i, m.sound_num, m.pos, CollectSound(sound_name)))

    client_positions = get_client_positions(demo, viewent_num)

    changeable_collections = [[] for _ in range(len(demo.blocks))]
    for event in sound_pickup_events:
        client_origin = client_positions[event.block_index]
        distance = max([abs(x-y) for x, y in zip(event.origin, client_origin)])
        assert distance < 5.0  # this is so large due to SV_StartSound taking the middle of maxs and mins

        distance = math.inf
        closest_item, distance = find_closest_item_to_client(client_origin,
            [item for item in items_by_frame[event.block_index-1]
             if item.type.collect_sound == event.sound], event.block_index)
        if distance >= 0.5:
            # this was needed for e1m5_009. host spawns directly in healthpack
            # which seems to be picked up instantly, so it is not even shown by
            # one frame
            closest_item, distance = find_closest_item_to_client(client_origin,
                [item for item in static_collectable_items.values()
                 if item.type.collect_sound == event.sound], event.block_index-1)
        if distance < 0.5:
            assert event.sound == closest_item.type.collect_sound
            closest_item.sound_event = event
            # TODO allow multiple items per sound event
            changeable_collections[event.block_index].append(closest_item)
    return changeable_collections


def get_backpack_collections(demo):
    models_precache, sounds_precache = get_precaches(demo)
    backpacks_by_frame = [[] for _ in range(len(demo.blocks))]
    sound_pickup_events = []
    viewent_num = get_viewent_num(demo)
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.EntityUpdateMessage):
                if m.modelindex and models_precache[m.modelindex] == b'progs/backpack.mdl':
                    backpacks_by_frame[i].append(CollectableItem(
                        m.num, m.origin, CollectableItemBackpack, None, math.inf))
            elif isinstance(m, messages.SoundMessage):
                if m.ent == viewent_num and sounds_precache[m.sound_num] ==  b'weapons/lock4.wav':
                    sound_pickup_events.append(SoundCollectEvent(
                        i, m.sound_num, m.pos, CollectableItemBackpack.collect_sound))
            # TODO: get backpack content from printed messages on next block

    client_positions = get_client_positions(demo, viewent_num)

    backpack_collections = [[] for _ in range(len(demo.blocks))]
    for event in sound_pickup_events:
        client_origin = client_positions[event.block_index]
        distance = max([abs(x-y) for x, y in zip(event.origin, client_origin)])
        assert distance < 5.0  # this is so large due to SV_StartSound taking the middle of maxs and mins

        for backpack in backpacks_by_frame[event.block_index-1]:
            if collision.distance(collision.bounds_player(client_origin),
                                  collision.bounds_item(backpack.origin, backpack.type.mins, backpack.type.maxs)) < 0.5:
                backpack_collections[event.block_index].append(backpack)
    return backpack_collections

def get_possible_collections(demo):
    models_precache, _ = get_precaches(demo)
    static_collectable_items = get_collectable_items(demo, models_precache)
    client_positions = get_client_positions(demo, get_viewent_num(demo))

    possible_pickups = [[] for _ in range(len(demo.blocks))]
    for i, pos in enumerate(client_positions):
        for item in static_collectable_items.values():
            tolerance = 0.0
            if i == 3:
                tolerance = 0.5  # for the instant pickup on e1m5_009
            # somehow need frame=i-2 for e1m3_023?
            if collision.distance(collision.bounds_player(pos),
                                  item.bounds(frame=i-2)) < tolerance:
                possible_pickups[i].append(item)
    return possible_pickups

def get_damage(demo):
    damage = []
    for block in demo.blocks:
        damage_messages = [m for m in block.messages
                           if isinstance(m, messages.DamageMessage)]
        assert len(damage_messages) == 1 or len(damage_messages) == 0
        if len(damage_messages) == 0:
            damage.append(messages.DamageMessage(0, 0, []))
        else:
            damage.append(damage_messages[0])
    return damage


def get_ammo_for_activeweapon(stats: format.ClientStats):
    if stats.activeweapon == 0:  # axe
        return 0, 0
    elif stats.activeweapon == ItemFlags.SHOTGUN:
        return ItemFlags.SHELLS, stats.shells
    elif stats.activeweapon == ItemFlags.SUPER_SHOTGUN:
        return ItemFlags.SHELLS, stats.shells
    elif stats.activeweapon == ItemFlags.NAILGUN:
        return ItemFlags.NAILS, stats.nails
    elif stats.activeweapon == ItemFlags.SUPER_NAILGUN:
        return ItemFlags.NAILS, stats.nails
    elif stats.activeweapon == ItemFlags.GRENADE_LAUNCHER:
        return ItemFlags.ROCKETS, stats.rockets
    elif stats.activeweapon == ItemFlags.ROCKET_LAUNCHER:
        return ItemFlags.ROCKETS, stats.rockets
    elif stats.activeweapon == ItemFlags.LIGHTNING:
        return ItemFlags.CELLS, stats.cells
    else:
        raise ValueError("Unknown activeweapon")

def rebuild_stats(new_start: format.ClientStats,
                  old_stats_list: list[format.ClientStats],
                  backpack_collections, possible_collections, damage, is_coop):
    assert len(old_stats_list) == len(damage)

    old_stats_previous = None
    stats = copy.deepcopy(new_start)
    stats_list = []
    actual_collections = [[] for _ in range(len(possible_collections))]

    for i, old_stats in enumerate(old_stats_list):
        if not old_stats:
            stats_list.append(None)
            continue
        if not old_stats_previous:
            old_stats_previous = copy.deepcopy(old_stats)
            old_stats_previous.health = 0  # so that instant pickup on e1m5_009 works

        if old_stats.armor == 0:
            orig_damage = damage[i].blood + damage[i].armor
        else:
            old_damage_reduction = get_damage_reduction(old_stats.items)
            orig_damage = math.floor(damage[i].armor / old_damage_reduction)

        damage_reduction = get_damage_reduction(stats.items)
        net_damage_armor = min(stats.armor, math.ceil(orig_damage * damage_reduction))
        net_damage_health = math.ceil(orig_damage - net_damage_armor)

        stats.armor -= net_damage_armor
        if stats.armor == 0:
            stats.items &= ~(ItemFlags.ARMOR1|ItemFlags.ARMOR2|ItemFlags.ARMOR3)
        if old_stats.health < old_stats_previous.health:
            if net_damage_armor == damage[i].armor:
                stats.health += old_stats.health - old_stats_previous.health
            else:
                stats.health -= net_damage_health
        #assert stats.health >= MIN_HEALTH
        assert stats.armor >= 0

        lost_shells = max(0, old_stats_previous.shells - old_stats.shells)
        lost_nails = max(0, old_stats_previous.nails - old_stats.nails)
        lost_rockets = max(0, old_stats_previous.rockets - old_stats.rockets)
        lost_cells = max(0, old_stats_previous.cells - old_stats.cells)

        stats.shells -= lost_shells
        stats.nails -= lost_nails
        stats.rockets -= lost_rockets
        stats.cells -= lost_cells
        assert stats.shells >= MIN_SHELLS
        assert stats.nails >= MIN_NAILS
        assert stats.rockets >= MIN_ROCKETS
        assert stats.cells >= MIN_CELLS

        for item in possible_collections[i]:
            if item.will_collect(stats, is_coop) and item.frame_collected > i:
                collected_health = item.get_pickup_health()
                collected_shells = item.get_pickup_shells()
                collected_nails = item.get_pickup_nails()
                collected_rockets = item.get_pickup_rockets()
                collected_cells = item.get_pickup_cells()
                collected_armor = item.get_pickup_armor()
                # TODO should really check if this specific item was picked up on this frame in the
                # original instead.
                picked_something_up_in_original = (
                    (collected_health > 0 and old_stats.health > old_stats_previous.health) or
                    (collected_shells > 0 and old_stats.shells > old_stats_previous.shells) or
                    (collected_nails > 0 and old_stats.nails > old_stats_previous.nails) or
                    (collected_rockets > 0 and old_stats.rockets > old_stats_previous.rockets) or
                    (collected_cells > 0 and old_stats.cells > old_stats_previous.cells) or
                    (collected_armor > 0 and old_stats.armor > old_stats_previous.armor))
                if item.will_collect(old_stats_previous, is_coop) and not picked_something_up_in_original:
                    # for some reason this item wasnt picked up in original demo
                    # despite stats indicating that it will be picked up. perhaps
                    # another coop player already got that item or something weird
                    # is going on like with the nailgun in the trap on e1m3
                    continue

                actual_collections[i].append(item)
                item.frame_collected = i

                stats.items |= item.get_pickup_items()
                if stats.items & ItemFlags.SUPERHEALTH:
                    stats.health = min(250, stats.health + collected_health)
                else:
                    stats.health = min(MAX_HEALTH, stats.health + collected_health)
                stats.shells = min(MAX_SHELLS, stats.shells + collected_shells)
                stats.nails = min(MAX_NAILS, stats.nails + collected_nails)
                stats.rockets = min(MAX_ROCKETS, stats.rockets + collected_rockets)
                stats.cells = min(MAX_NAILS, stats.cells + collected_cells)
                if collected_armor > 0:
                    stats.armor = collected_armor

        added_items = (old_stats.items & ~old_stats_previous.items)
        removed_items = (~old_stats.items & old_stats_previous.items)
        stats.items |= added_items
        stats.items &= ~removed_items

        if backpack_collections[i]:
            if old_stats.shells > old_stats_previous.shells:
                # TODO assert no other shells collection, that would make things difficult
                backpack_shells = old_stats.shells - old_stats_previous.shells
                stats.shells = min(MAX_SHELLS, stats.shells + backpack_shells)
            if old_stats.nails > old_stats_previous.nails:
                # TODO assert no other nails collection, that would make things difficult
                backpack_nails = old_stats.nails - old_stats_previous.nails
                stats.nails = min(MAX_NAILS, stats.nails + backpack_nails)
            if old_stats.rockets > old_stats_previous.rockets:
                # TODO assert no other rockets collection, that would make things difficult
                backpack_rockets = old_stats.rockets - old_stats_previous.rockets
                stats.rockets = min(MAX_ROCKETS, stats.rockets + backpack_rockets)
            if old_stats.cells > old_stats_previous.cells:
                # TODO assert no other cells collection, that would make things difficult
                backpack_cells = old_stats.cells - old_stats_previous.cells
                stats.cells = min(MAX_NAILS, stats.cells + backpack_cells)
            assert (old_stats.shells > old_stats_previous.shells or
                    old_stats.nails > old_stats_previous.nails or
                    old_stats.rockets > old_stats_previous.rockets or
                    old_stats.cells > old_stats_previous.cells)

        stats.activeweapon = old_stats.activeweapon  # TODO: set to new_start first. then set to something else if 0 ammo is reached. Also fix which ammo is shown in hud with that
        ammo_item_flag, stats.ammo = get_ammo_for_activeweapon(stats)
        if ammo_item_flag != 0 and stats.ammo <= 0:
            pass  # TODO: switch in the next x frames
            #raise ValueError("This weapon cannot be active")
        stats.items &= ~(ItemFlags.SHELLS|ItemFlags.NAILS|ItemFlags.ROCKETS|ItemFlags.CELLS)
        stats.items |= ammo_item_flag

        stats_list.append(copy.deepcopy(stats))
        old_stats_previous = old_stats
    return stats_list, actual_collections


def fix_collection_events(actual_collections, demo):
    _, sounds_precache = get_precaches(demo)
    changeable_collections = get_changeable_collections(demo)
    viewent_num = get_viewent_num(demo)
    client_positions = get_client_positions(demo, viewent_num)

    blocks_to_remove = []
    for i, block in enumerate(demo.blocks):
        equal = []
        for x in changeable_collections[i]:
            for y in actual_collections[i]:
                if x.entity_num == y.entity_num:
                    equal.append(x.entity_num)
        collections_to_remove = [c for c in changeable_collections[i] if c.entity_num not in equal]
        collections_to_add = [c for c in actual_collections[i] if c.entity_num not in equal]

        for c in collections_to_remove:
            print("removed:", c.type)

            sounds_to_remove = [m for m in block.messages
                                if (isinstance(m, messages.SoundMessage) and
                                    m.sound_num == c.sound_event.sound_num)]
            assert len(sounds_to_remove) == 1
            block.messages.remove(sounds_to_remove[0])

            # TODO: assert that this really is the info block for this pickup with
            # pickup message, screenflash and so on
            blocks_to_remove.append(i + 1)

            # TODO: can we somehow figure out if the item is in view to not spam
            # these messages in every block?
            flags = messages.UpdateFlags.SIGNAL
            if c.entity_num > 255:
                flags |= messages.UpdateFlags.MOREBITS|messages.UpdateFlags.LONGENTITY
            message = messages.EntityUpdateMessage(
                flags, c.entity_num, None, None, None, None, None, None, None,
                None, None, None, None, None, None)
            for j in range(i, len(demo.blocks)):
                if any([isinstance(m, messages.TimeMessage) for m in demo.blocks[j].messages]):
                    demo.blocks[j].messages.append(message)

        for c in collections_to_add:
            print("added:", c.type)

            sound_name = c.type.collect_sound.value
            sound_num = sounds_precache.index(sound_name)
            block.messages.append(messages.SoundMessage(flags=0, volume=255,
                attenuation=1.0, ent=viewent_num, channel=3, sound_num=sound_num,
                pos=collision.PlayerBounds.center(client_positions[i])))
            block.messages.append(messages.PrintMessage(text=c.type.print_text))
            block.messages.append(messages.StuffTextMessage(text=b'bf\n'))
            for j in range(i, len(demo.blocks)):
                for m in [m for m in demo.blocks[j].messages if isinstance(m, messages.EntityUpdateMessage) and m.num == c.entity_num]:
                    demo.blocks[j].messages.remove(m)

    for i in reversed(blocks_to_remove):
        del demo.blocks[i]
