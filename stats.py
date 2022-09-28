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

@dataclasses.dataclass
class Health:
    name = 'health'
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        if items & ItemFlags.SUPERHEALTH:
            return min(value, MAX_MEGAHEALTH)
        else:
            return min(value, MAX_HEALTH)

@dataclasses.dataclass
class Shells:
    name = 'shells'
    min = MIN_SHELLS
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        return min(value, MAX_SHELLS)

@dataclasses.dataclass
class Nails:
    name = 'nails'
    min = MIN_NAILS
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        return min(value, MAX_NAILS)

@dataclasses.dataclass
class Rockets:
    name = 'rockets'
    min = MIN_ROCKETS
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        return min(value, MAX_ROCKETS)

@dataclasses.dataclass
class Cells:
    name = 'cells'
    min = MIN_CELLS
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        return min(value, MAX_CELLS)

@dataclasses.dataclass
class Armor:
    value: int

@dataclasses.dataclass
class Item:
    value: ItemFlags

# Convenience wrapper around ClientStats to be able to access it dynamically
# with above stat types
class ClientStatsAccessor(format.ClientStats):
    def __init__(self, data: format.ClientStats):
        super().__init__(data.items, data.health, data.armor, data.shells,
                         data.nails, data.rockets, data.cells,
                         data.activeweapon, data.ammo)
    def __getitem__(self, stat_type):
        return getattr(self, stat_type.name)
    def __setitem__(self, stat_type, value):
        setattr(self, stat_type.name, value)


def get_damage_reduction(items: ItemFlags) -> float:
    damage_reduction = 0.0
    if items & ItemFlags.ARMOR1:
        damage_reduction = 0.3
    elif items & ItemFlags.ARMOR2:
        damage_reduction = 0.6
    elif items & ItemFlags.ARMOR3:
        damage_reduction = 0.8
    return damage_reduction

class CollectableHealth15:
    gives = [Health(15)]
    collect_sound = CollectSound.HP15
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 15 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.health < MAX_HEALTH

class CollectableHealth25:
    gives = [Health(25)]
    collect_sound = CollectSound.HP25
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 25 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.health < MAX_HEALTH

class CollectableHealth100:
    gives = [Item(ItemFlags.SUPERHEALTH), Health(100)]
    collect_sound = CollectSound.HP100
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 100 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return True

class CollectableShells20:
    gives = [Shells(20)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the shells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.shells < MAX_SHELLS

class CollectableShells40:
    gives = [Shells(40)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the shells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.shells < MAX_SHELLS

class CollectableNails25:
    gives = [Nails(25)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the nails\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.nails < MAX_NAILS

class CollectableNails50:
    gives = [Nails(50)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the nails\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.nails < MAX_NAILS

class CollectableRockets5:
    gives = [Rockets(5)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the rockets\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.rockets < MAX_ROCKETS

class CollectableRockets10:
    gives = [Rockets(10)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the rockets\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.rockets < MAX_ROCKETS

class CollectableCells6:
    gives = [Cells(6)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the cells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.cells < MAX_CELLS

class CollectableCells12:
    gives = [Cells(12)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the cells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.cells < MAX_CELLS

class CollectableGreenArmor:
    armor_value = 100
    gives = [Item(ItemFlags.ARMOR1), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR1) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)

class CollectableYellowArmor:
    armor_value = 150
    gives = [Item(ItemFlags.ARMOR2), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR2) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)

class CollectableRedArmor:
    armor_value = 200
    gives = [Item(ItemFlags.ARMOR3), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR3) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)

class CollectableSuperShotgun:
    gives = [Item(ItemFlags.SUPER_SHOTGUN), Shells(5)]
    collect_sound = CollectSound.WEAPON
    print_text = b"You got the Double-barrelled Shotgun\n"
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.SUPER_SHOTGUN)

class CollectableNailgun:
    gives = [Item(ItemFlags.NAILGUN), Nails(30)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the nailgun\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.NAILGUN)

class CollectableSuperNailgun:
    gives = [Item(ItemFlags.SUPER_NAILGUN), Nails(30)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Super Nailgun\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.SUPER_NAILGUN)

class CollectableGrenadeLauncher:
    gives = [Item(ItemFlags.GRENADE_LAUNCHER), Rockets(5)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Grenade Launcher\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.GRENADE_LAUNCHER)

class CollectableRocketLauncher:
    gives = [Item(ItemFlags.ROCKET_LAUNCHER), Rockets(5)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Rocket Launcher\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.ROCKET_LAUNCHER)

class CollectableLightningGun:
    gives = [Item(ItemFlags.LIGHTNING), Cells(15)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Thunderbolt\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.LIGHTNING)

@dataclasses.dataclass
class CollectableBackpack:
    gives = [Shells(math.inf), Nails(math.inf), Rockets(math.inf), Cells(math.inf)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]

    @staticmethod
    def will_collect(stats, is_coop):
        return True


COLLECTABLE_MODELS_MAP = {
    b'maps/b_bh10.bsp': CollectableHealth15,
    b'maps/b_bh25.bsp': CollectableHealth25,
    b'maps/b_bh100.bsp': CollectableHealth100,
    b'maps/b_shell0.bsp': CollectableShells20,
    b'maps/b_shell1.bsp': CollectableShells40,
    b'maps/b_nail0.bsp': CollectableNails25,
    b'maps/b_nail1.bsp': CollectableNails50,
    b'maps/b_rock0.bsp': CollectableRockets5,
    b'maps/b_rock1.bsp': CollectableRockets10,
    b'maps/b_batt0.bsp': CollectableCells6,
    b'maps/b_batt1.bsp': CollectableCells12,
    b'progs/armor.mdl': None,  # depends on skin, so has to be handled in special way
    b'progs/g_shot.mdl': CollectableSuperShotgun,
    b'progs/g_nail.mdl': CollectableNailgun,
    b'progs/g_nail2.mdl': CollectableSuperNailgun,
    b'progs/g_rock.mdl': CollectableGrenadeLauncher,
    b'progs/g_rock2.mdl': CollectableRocketLauncher,
    b'progs/g_light.mdl': CollectableLightningGun,
}

@dataclasses.dataclass
class SoundCollectEvent:
    block_index: int
    sound_num: int
    origin: list[float]
    sound: CollectSound

@dataclasses.dataclass
class Collectable:
    entity_num: int
    type: None
    sound_event: SoundCollectEvent
    frame_collected: int

    def will_collect(self, stats, is_coop):
        return self.type.will_collect(stats, is_coop)

    def get_pickup(self, stat_type):
        return sum(x.value for x in self.type.gives if isinstance(x, stat_type))
    def get_pickup_items(self):
        item_flags = 0
        for flags in [x.value for x in self.type.gives if isinstance(x, Item)]:
            item_flags |= flags
        return item_flags

    def bounds(self, origin):
        return collision.bounds_collectable(origin, self.type.mins, self.type.maxs)

@dataclasses.dataclass
class CollectablePersistant:
    collectable: Collectable
    origins: list[list[float]]

    def bounds(self, frame: int):
        return self.collectable.bounds(self.origins[frame])

@dataclasses.dataclass
class CollectableActiveFrame:
    collectable: Collectable
    origin: list[float]

    def bounds(self):
        return self.collectable.bounds(self.origin)


def get_precaches(demo):
    server_info_message = [m for b in demo.blocks for m in b.messages
                           if isinstance(m, messages.ServerInfoMessage)]
    assert len(server_info_message) == 1
    return (server_info_message[0].models_precache,
            server_info_message[0].sounds_precache)

def get_static_collectables(demo, models_precache):
    collectables_static = dict()
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.SpawnBaselineMessage):
                model_name = models_precache[m.modelindex]
                if model_name in COLLECTABLE_MODELS_MAP.keys():
                    assert m.entity_num not in collectables_static
                    if model_name == b'progs/armor.mdl':
                        if m.skin == 0:
                            collectable_type = CollectableGreenArmor
                        elif m.skin == 1:
                            collectable_type = CollectableYellowArmor
                        else:
                            assert m.skin == 2
                            collectable_type = CollectableRedArmor
                    else:
                        collectable_type = COLLECTABLE_MODELS_MAP[model_name]
                    collectables_static[m.entity_num] = CollectablePersistant(
                        Collectable(m.entity_num, collectable_type, None, math.inf),
                        [list(m.origin) for _ in range(len(demo.blocks))])
            elif isinstance(m, messages.EntityUpdateMessage):
                if m.num in collectables_static:
                    if m.flags & messages.UpdateFlags.ORIGIN1:
                        collectables_static[m.num].origins[i][0] = m.origin[0]
                    if m.flags & messages.UpdateFlags.ORIGIN2:
                        collectables_static[m.num].origins[i][1] = m.origin[1]
                    if m.flags & messages.UpdateFlags.ORIGIN3:
                        collectables_static[m.num].origins[i][2] = m.origin[2]
    return collectables_static

def get_static_collectables_by_frame(demo, models_precache):
    statics = get_static_collectables(demo, models_precache)
    collectables_by_frame = [[] for _ in range(len(demo.blocks))]
    for i, block in enumerate(demo.blocks):
        has_entity_update = False
        for m in block.messages:
            if isinstance(m, messages.SpawnBaselineMessage):
                # this is so that we can collect items instantly on unpause,
                # because there is not a single EntityUpdateMessage for those
                if m.entity_num in statics:
                    assert i == 1
                    collectables_by_frame[i].append(CollectableActiveFrame(
                        statics[m.entity_num].collectable,
                        statics[m.entity_num].origins[i]))
            elif isinstance(m, messages.EntityUpdateMessage):
                if m.num in statics:
                    has_entity_update = True
                    collectables_by_frame[i].append(CollectableActiveFrame(
                        statics[m.num].collectable, statics[m.num].origins[i]))
        if not any((isinstance(m, messages.TimeMessage) or
                    isinstance(m, messages.SpawnBaselineMessage))
                   for m in block.messages):
            assert not has_entity_update
            # this is so that intermediate frames that do not have a TimeMessage
            # still provide the info as if accessing the proper frame
            collectables_by_frame[i] = collectables_by_frame[i-1]
    return collectables_by_frame

def get_backpacks_by_frame(demo, models_precache):
    backpacks_by_frame = [[] for _ in range(len(demo.blocks))]
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.EntityUpdateMessage):
                if m.modelindex and models_precache[m.modelindex] == b'progs/backpack.mdl':
                    backpacks_by_frame[i].append(CollectableActiveFrame(
                        Collectable(m.num, CollectableBackpack, None, math.inf),
                        m.origin))
    return backpacks_by_frame

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

def is_sound_from_client_position(client_origin, sound_origin) -> bool:
    assert len(client_origin) == len(sound_origin) == 3
    # sounds are created at center of bounding box, see SV_StartSound
    client_center = collision.PlayerBounds.center(client_origin)
    max_diff = max(abs(x - y) for x, y in zip(client_center, sound_origin))
    # can't check for equality as this does not seem to be accurate all the time
    # for some reason... Perhaps the client origin can change slightly between
    # an entity update and when the sound is created.
    return max_diff < 1.5

def find_closest_collectable_to_client(client_origin, collectable_active_frames):
    closest_distance = math.inf
    closest_collectable = None
    for collectable_frame in collectable_active_frames:
        distance = collision.distance(collision.bounds_player(client_origin),
                                      collectable_frame.bounds())
        if distance < closest_distance:
            closest_collectable = collectable_frame.collectable
            closest_distance = distance
    return closest_collectable, closest_distance

def get_collections(demo):
    models_precache, sounds_precache = get_precaches(demo)
    sound_pickup_events = []
    viewent_num = get_viewent_num(demo)
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.SoundMessage):
                sound_name = sounds_precache[m.sound_num]
                if m.ent == viewent_num and sound_name in COLLECT_SOUNDS:
                    sound_pickup_events.append(SoundCollectEvent(
                        i, m.sound_num, m.pos, CollectSound(sound_name)))

    statics_by_frame = get_static_collectables_by_frame(demo, models_precache)
    backpacks_by_frame = get_backpacks_by_frame(demo, models_precache)
    client_positions = get_client_positions(demo, viewent_num)

    static_collections = [[] for _ in range(len(demo.blocks))]
    backpack_collections = [[] for _ in range(len(demo.blocks))]
    for event in sound_pickup_events:
        client_origin = client_positions[event.block_index]
        assert is_sound_from_client_position(client_origin=client_origin,
                                             sound_origin=event.origin)

        statics_candidates = [static for static in statics_by_frame[event.block_index-1]
                              if static.collectable.type.collect_sound == event.sound]
        closest_static, distance_static = find_closest_collectable_to_client(
            client_origin, statics_candidates)

        closest_backpack = None
        distance_backpack = math.inf
        if event.sound == CollectSound.AMMO:
            closest_backpack, distance_backpack = find_closest_collectable_to_client(
                client_origin, backpacks_by_frame[event.block_index-1])

        if distance_static < distance_backpack:
            distance = distance_static
            closest = closest_static
            static_collections[event.block_index].append(closest_static)
        else:
            distance = distance_backpack
            closest = closest_backpack
            backpack_collections[event.block_index].append(closest_backpack)
        # TODO: allow multiple collectables per sound event
        # probably just have to remove closest from the statics_by_frame or
        # backpacks_by_frame lists?
        assert distance < 0.5
        assert event.sound == closest.type.collect_sound
        closest.sound_event = event

    return static_collections, backpack_collections

def get_static_collections(demo):
    static_collections, _ = get_collections(demo)
    return static_collections

def get_backpack_collections(demo):
    _, backpack_collections = get_collections(demo)
    return backpack_collections

def get_possible_collections(demo):
    models_precache, _ = get_precaches(demo)
    collectables = get_static_collectables(demo, models_precache)
    client_positions = get_client_positions(demo, get_viewent_num(demo))

    possible_pickups = [[] for _ in range(len(demo.blocks))]
    for i, pos in enumerate(client_positions):
        for collectable in collectables.values():
            tolerance = 0.0
            if i == 3:
                tolerance = 0.5  # for the instant pickup on e1m5_009
            # somehow need frame=i-2 for e1m3_023?
            if collision.distance(collision.bounds_player(pos),
                                  collectable.bounds(frame=i-2)) <= tolerance:
                possible_pickups[i].append(collectable.collectable)
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
                  backpack_collections, old_static_collections,
                  possible_collections, damage, is_coop):
    assert len(old_stats_list) == len(damage)

    old_stats_previous = None
    stats = ClientStatsAccessor(copy.deepcopy(new_start))
    stats_list = []
    actual_collections = [[] for _ in range(len(possible_collections))]

    for i, old_stats_data in enumerate(old_stats_list):
        if not old_stats_data:
            stats_list.append(None)
            continue
        old_stats = ClientStatsAccessor(old_stats_data)
        if not old_stats_previous:
            old_stats_previous = old_stats

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

        for stat_type in (Shells, Nails, Rockets, Cells):
            lost = max(0, old_stats_previous[stat_type] - old_stats[stat_type])
            stats[stat_type] -= lost
            assert stats[stat_type] >= stat_type.min

        for collectable in possible_collections[i]:
            if collectable.will_collect(stats, is_coop) and collectable.frame_collected > i:
                picked_up_in_original = any(c.entity_num == collectable.entity_num for c in old_static_collections[i])
                if collectable.will_collect(old_stats_previous, is_coop) and not picked_up_in_original:
                    # for some reason this collectable wasnt picked up in original demo
                    # despite stats indicating that it will be picked up. perhaps
                    # another coop player already got that collectable or something weird
                    # is going on like with the nailgun in the trap on e1m3
                    continue

                actual_collections[i].append(collectable)
                collectable.frame_collected = i

                stats.items |= collectable.get_pickup_items()
                for stat_type in (Health, Shells, Nails, Rockets, Cells):
                    collected_value = collectable.get_pickup(stat_type)
                    stats[stat_type] = stat_type.bound(
                        stats[stat_type] + collected_value, stats.items)
                collected_armor = collectable.get_pickup(Armor)
                if collected_armor > 0:
                    stats.armor = collected_armor

        added_items = (old_stats.items & ~old_stats_previous.items)
        removed_items = (~old_stats.items & old_stats_previous.items)
        stats.items |= added_items
        stats.items &= ~removed_items

        if backpack_collections[i]:
            for stat_type in (Shells, Nails, Rockets, Cells):
                # TODO assert no other collection of this stat_type, that would
                # make things difficult
                if old_stats[stat_type] > old_stats_previous[stat_type]:
                    backpack_value = (old_stats[stat_type] -
                                      old_stats_previous[stat_type])
                    stats[stat_type] = stat_type.bound(
                        stats[stat_type] + backpack_value, stats.items)
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
    models_precache, sounds_precache = get_precaches(demo)
    changeable_collections = get_static_collections(demo)
    viewent_num = get_viewent_num(demo)
    client_positions = get_client_positions(demo, viewent_num)

    static_collectables = get_static_collectables(demo, models_precache)

    times = demo.get_time()
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
            print(f"removed collection: {c.type} at time {times[i]}")

            sounds_to_remove = [m for m in block.messages
                                if (isinstance(m, messages.SoundMessage) and
                                    m.sound_num == c.sound_event.sound_num)]
            assert len(sounds_to_remove) == 1
            block.messages.remove(sounds_to_remove[0])

            # TODO: assert that this really is the info block for this pickup with
            # pickup message, screenflash and so on
            blocks_to_remove.append(i + 1)

            # TODO: can we somehow figure out if the collectable is in view to not spam
            # these messages in every block?
            flags = messages.UpdateFlags.SIGNAL
            if c.entity_num > 255:
                flags |= messages.UpdateFlags.MOREBITS|messages.UpdateFlags.LONGENTITY
            last_origin = None
            if (static_collectables[c.entity_num].origins[i-1] !=
                static_collectables[c.entity_num].origins[0]):
                last_origin = static_collectables[c.entity_num].origins[i-1]
                flags |= (messages.UpdateFlags.ORIGIN1|
                          messages.UpdateFlags.ORIGIN2|
                          messages.UpdateFlags.ORIGIN3)
            message = messages.EntityUpdateMessage(
                flags, c.entity_num, None, None, None, None, None, last_origin,
                None, None, None, None, None, None, None)
            for j in range(i, len(demo.blocks)):
                if any([isinstance(m, messages.TimeMessage) for m in demo.blocks[j].messages]):
                    demo.blocks[j].messages.append(message)

        for c in collections_to_add:
            print(f"added collection: {c.type} at time {times[i]}")

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
