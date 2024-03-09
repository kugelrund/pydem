import dataclasses
import enum
import math

from . import bindata


class ProtocolVersion(enum.IntEnum):
    NETQUAKE = 15
    FITZQUAKE = 666
    RMQ = 999


# this should be (enum.IntFlag), but that has terrible performance with the
# bitwise and operator. So instead let's use plain int
class ProtocolFlags:
    PRFL_SHORTANGLE = (1 << 1)
    PRFL_FLOATANGLE = (1 << 2)
    PRFL_24BITCOORD = (1 << 3)
    PRFL_FLOATCOORD = (1 << 4)
    PRFL_EDICTSCALE = (1 << 5)
    PRFL_ALPHASANITY = (1 << 6)
    PRFL_INT32COORD = (1 << 7)

protocol = ProtocolVersion.NETQUAKE  # TODO
protocol_flags = 0  # TODO


def read_coord(protocol_flags: int, stream) -> float:
    if protocol_flags & ProtocolFlags.PRFL_FLOATCOORD:
        return bindata.read_f32(stream)
    elif protocol_flags & ProtocolFlags.PRFL_INT32COORD:
        return bindata.read_i32(stream) * (1.0/16.0)
    elif protocol_flags & ProtocolFlags.PRFL_24BITCOORD:
        return bindata.read_i16(stream) + bindata.read_i8(stream) * (1.0/255.0)
    else:
        return bindata.read_i16(stream) * (1.0/8.0)

def write_coord(protocol_flags: int, stream, value: float):
    if protocol_flags & ProtocolFlags.PRFL_FLOATCOORD:
        bindata.write_f32(stream, value)
    elif protocol_flags & ProtocolFlags.PRFL_INT32COORD:
        bindata.write_i32(stream, round(value * 16.0))
    elif protocol_flags & ProtocolFlags.PRFL_24BITCOORD:
        frac_part, int_part = math.modf(value) 
        bindata.write_i16(stream, int(int_part))
        bindata.write_i8(stream, round(frac_part * 255.0))
    else:
        bindata.write_i16(stream, round(value * 8.0))

def read_coord_n(protocol_flags: int, stream, n: int):
    return [read_coord(protocol_flags, stream) for _ in range(n)]

def write_coord_n(protocol_flags: int, stream, values: list[float]):
    for value in values:
        write_coord(protocol_flags, stream, value)

def read_angle(protocol_flags: int, stream) -> float:
    if protocol_flags & ProtocolFlags.PRFL_FLOATANGLE:
        return bindata.read_f32(stream)
    elif protocol_flags & ProtocolFlags.PRFL_SHORTANGLE:
        return bindata.read_i16(stream) * (360.0/65536.0)
    else:
        return bindata.read_i8(stream) * (360.0/256.0)

def write_angle(protocol_flags: int, stream, value: float):
    if protocol_flags & ProtocolFlags.PRFL_FLOATANGLE:
        bindata.write_f32(stream, value)
    elif protocol_flags & ProtocolFlags.PRFL_SHORTANGLE:
        bindata.write_i16(stream, round(value / (360.0/65536.0)))
    else:
        bindata.write_i8(stream, round(value / (360.0/256.0)))

def read_angle_n(protocol_flags: int, stream, n: int):
    return [read_angle(protocol_flags, stream) for _ in range(n)]

def write_angle_n(protocol_flags: int, stream, values: list[float]):
    for value in values:
        write_angle(protocol_flags, stream, value)


@dataclasses.dataclass
class BadMessage:
    ID = 0

    def write(self, stream):
        bindata.write_u8(stream, self.ID)

    @staticmethod
    def parse(stream):
        return BadMessage()


@dataclasses.dataclass
class NopMessage:
    ID = 1

    def write(self, stream):
        bindata.write_u8(stream, self.ID)

    @staticmethod
    def parse(stream):
        return NopMessage()


@dataclasses.dataclass
class DisconnectMessage:
    ID = 2

    def write(self, stream):
        bindata.write_u8(stream, self.ID)

    @staticmethod
    def parse(stream):
        return DisconnectMessage()


@dataclasses.dataclass
class UpdateStatMessage:
    ID = 3

    stat_id: int
    stat_value: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.stat_id)
        bindata.write_i32(stream, self.stat_value)

    @staticmethod
    def parse(stream):
        stat_id = bindata.read_u8(stream)
        stat_value = bindata.read_i32(stream)
        return UpdateStatMessage(stat_id, stat_value)


@dataclasses.dataclass
class VersionMessage:
    ID = 4

    protocol: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_i32(stream, self.protocol)

    @staticmethod
    def parse(stream):
        return VersionMessage(protocol=bindata.read_i32(stream))


@dataclasses.dataclass
class SetViewMessage:
    ID = 5

    viewentity_id: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_i16(stream, self.viewentity_id)

    @staticmethod
    def parse(stream):
        return SetViewMessage(viewentity_id=bindata.read_i16(stream))


class SoundFlags(enum.IntFlag):
    VOLUME = (1<<0)
    ATTENUATION = (1<<1)
    LOOPING = (1<<2)
    # Protocol.FITZQUAKE
    LARGEENTITY	= (1<<3)
    LARGESOUND = (1<<4)

@dataclasses.dataclass
class SoundMessage:
    ID = 6
    DEFAULT_SOUND_PACKET_VOLUME = 255
    DEFAULT_SOUND_PACKET_ATTENUATION = 1.0

    flags: SoundFlags
    volume: int
    attenuation: int
    ent: int
    channel: int
    sound_num: int
    pos: list[float]

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.flags)

        if self.flags & SoundFlags.VOLUME:
            bindata.write_u8(stream, self.volume)
        if self.flags & SoundFlags.ATTENUATION:
            bindata.write_u8(stream, self.attenuation)

        if self.flags & SoundFlags.LARGEENTITY:
            bindata.write_u16(stream, self.ent)
            bindata.write_u8(stream, self.channel)
        else:
            bindata.write_u16(stream, (self.ent << 3) + self.channel)

        if self.flags & SoundFlags.LARGESOUND:
            bindata.write_u16(stream, self.sound_num)
        else:
            bindata.write_u8(stream, self.sound_num)

        write_coord_n(protocol_flags, stream, self.pos)

    @staticmethod
    def parse(stream):
        flags = SoundFlags(bindata.read_u8(stream))
        volume = bindata.read_u8(stream) if (flags & SoundFlags.VOLUME) else SoundMessage.DEFAULT_SOUND_PACKET_VOLUME
        attenuation = bindata.read_u8(stream) if (flags & SoundFlags.ATTENUATION) else SoundMessage.DEFAULT_SOUND_PACKET_ATTENUATION

        if flags & SoundFlags.LARGEENTITY:
            ent = bindata.read_u16(stream)
            channel = bindata.read_u8(stream)
        else:
            channel = bindata.read_u16(stream)
            ent = channel >> 3
            channel &= 7

        if flags & SoundFlags.LARGESOUND:
            sound_num = bindata.read_u16(stream)
        else:
            sound_num = bindata.read_u8(stream)

        pos = read_coord_n(protocol_flags, stream, 3)

        return SoundMessage(flags, volume, attenuation, ent, channel, sound_num, pos)


@dataclasses.dataclass
class TimeMessage:
    ID = 7

    time: float

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_f32(stream, self.time)

    @staticmethod
    def parse(stream):
        return TimeMessage(time=bindata.read_f32(stream))


@dataclasses.dataclass
class PrintMessage:
    ID = 8

    text: str

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_c_str(stream, self.text)

    @staticmethod
    def parse(stream):
        return PrintMessage(text=bindata.read_c_str(stream))


@dataclasses.dataclass
class StuffTextMessage:
    ID = 9

    text: str

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_c_str(stream, self.text)

    @staticmethod
    def parse(stream):
        return StuffTextMessage(text=bindata.read_c_str(stream))


@dataclasses.dataclass
class SetAngleMessage:
    ID = 10

    yaw: float
    roll: float
    pitch: float

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        write_angle_n(protocol_flags, stream, [self.yaw, self.roll, self.pitch])

    @staticmethod
    def parse(stream):
        yaw, roll, pitch = read_angle_n(protocol_flags, stream, 3)
        return SetAngleMessage(yaw, roll, pitch)


@dataclasses.dataclass
class ServerInfoMessage:
    ID = 11

    protocol: ProtocolVersion
    protocol_flags: int
    max_clients: int
    gametype: int
    levelname: str
    models_precache: list[str]
    sounds_precache: list[str]

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u32(stream, self.protocol)
        if self.protocol == ProtocolVersion.RMQ:
            bindata.write_u32(stream, self.protocol_flags)
        bindata.write_u8(stream, self.max_clients)
        bindata.write_u8(stream, self.gametype)
        bindata.write_c_str(stream, self.levelname)

        for s in self.models_precache[1:]:
            bindata.write_c_str(stream, s)
        bindata.write_c_str(stream, b'')

        for s in self.sounds_precache[1:]:
            bindata.write_c_str(stream, s)
        bindata.write_c_str(stream, b'')

    @staticmethod
    def parse(stream):
        protocol = ProtocolVersion(bindata.read_u32(stream))
        protocol_flags = 0
        if protocol == ProtocolVersion.RMQ:
            protocol_flags = bindata.read_u32(stream)
        max_clients = bindata.read_u8(stream)
        gametype = bindata.read_u8(stream)
        levelname = bindata.read_c_str(stream)

        models_precache = [b'']
        s = bindata.read_c_str(stream)
        while s:
            models_precache.append(s)
            s = bindata.read_c_str(stream)

        sounds_precache = [b'']
        s = bindata.read_c_str(stream)
        while s:
            sounds_precache.append(s)
            s = bindata.read_c_str(stream)

        return ServerInfoMessage(protocol, protocol_flags, max_clients,
                                 gametype, levelname, models_precache,
                                 sounds_precache)


@dataclasses.dataclass
class LightstyleMessage:
    ID = 12

    index: int
    map: str

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.index)
        bindata.write_c_str(stream, self.map)

    @staticmethod
    def parse(stream):
        return LightstyleMessage(index=bindata.read_u8(stream),
                                 map=bindata.read_c_str(stream))


@dataclasses.dataclass
class UpdateNameMessage:
    ID = 13

    player_id: int
    name: str

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.player_id)
        bindata.write_c_str(stream, self.name)

    @staticmethod
    def parse(stream):
        return UpdateNameMessage(player_id=bindata.read_u8(stream),
                                 name=bindata.read_c_str(stream))


@dataclasses.dataclass
class UpdateFragsMessage:
    ID = 14

    player_id: int
    frags: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.player_id)
        bindata.write_i16(stream, self.frags)

    @staticmethod
    def parse(stream):
        return UpdateFragsMessage(player_id=bindata.read_u8(stream),
                                  frags=bindata.read_i16(stream))


class ServerUpdateFlags(enum.IntFlag):
    VIEWHEIGHT = (1<<0)
    IDEALPITCH = (1<<1)
    PUNCH1 = (1<<2)
    PUNCH2 = (1<<3)
    PUNCH3 = (1<<4)
    VELOCITY1 = (1<<5)
    VELOCITY2 = (1<<6)
    VELOCITY3 = (1<<7)
    ITEMS = (1<<9)
    ONGROUND = (1<<10)
    INWATER = (1<<11)
    WEAPONFRAME = (1<<12)
    ARMOR = (1<<13)
    WEAPON = (1<<14)
    # new bits for Protocol.FITZQUAKE
    EXTEND1 = (1<<15)
    WEAPON2 = (1<<16)
    ARMOR2 = (1<<17)
    AMMO2 = (1<<18)
    SHELLS2 = (1<<19)
    NAILS2 = (1<<20)
    ROCKETS2 = (1<<21)
    CELLS2 = (1<<22)
    EXTEND2 = (1<<23)
    WEAPONFRAME2 = (1<<24)
    WEAPONALPHA = (1<<25)
    UNUSED26 = (1<<26)
    UNUSED27 = (1<<27)
    UNUSED28 = (1<<28)
    UNUSED29 = (1<<29)
    UNUSED30 = (1<<30)
    EXTEND3 = (1<<31)

class ItemFlags(enum.IntFlag):
    SHOTGUN = 1
    SUPER_SHOTGUN = 2
    NAILGUN = 4
    SUPER_NAILGUN = 8
    GRENADE_LAUNCHER = 16
    ROCKET_LAUNCHER = 32
    LIGHTNING = 64
    SUPER_LIGHTNING = 128
    SHELLS = 256
    NAILS = 512
    ROCKETS = 1024
    CELLS = 2048
    AXE = 4096
    ARMOR1 = 8192
    ARMOR2 = 16384
    ARMOR3 = 32768
    SUPERHEALTH = 65536
    KEY1 = 131072
    KEY2 = 262144
    INVISIBILITY = 524288
    INVULNERABILITY = 1048576
    SUIT = 2097152
    QUAD = 4194304
    SIGIL1 = (1<<28)
    SIGIL2 = (1<<29)
    SIGIL3 = (1<<30)
    SIGIL4 = (1<<31)
    # activeweapon is only a byte, so AXE=4096 does not fit and will be cutoff
    # so for activeweapon, 0 corresponds to AXE. Should only be used for
    # activeweapon, and only by comparing for exact equality
    AXE_ACTIVEWEAPON = 0

@dataclasses.dataclass
class ClientDataMessage:
    ID = 15
    DEFAULT_VIEWHEIGHT = 22.0

    flags: ServerUpdateFlags
    viewheight: float
    idealpitch: float
    punchangle: list[float]
    velocity: list[float]
    items: ItemFlags
    weaponframe: int
    armor: int
    weapon: int
    health: int
    ammo: int
    shells: int
    nails: int
    rockets: int
    cells: int
    activeweapon: int
    weaponalpha: float

    def write(self, stream):
        # TODO: Need to add more to this if we change other data
        if self.armor:
            self.flags |= ServerUpdateFlags.ARMOR
        else:
            self.flags &= ~ServerUpdateFlags.ARMOR

        bindata.write_u8(stream, self.ID)
        bindata.write_u16(stream, self.flags & 0x0000ffff)
        if self.flags & ServerUpdateFlags.EXTEND1:
            bindata.write_u8(stream, (self.flags & 0x00ff0000) >> 16)
        if self.flags & ServerUpdateFlags.EXTEND2:
            bindata.write_u8(stream, self.flags >> 24)
        
        if self.flags & ServerUpdateFlags.VIEWHEIGHT:
            bindata.write_i8(stream, self.viewheight)
        if self.flags & ServerUpdateFlags.IDEALPITCH:
            bindata.write_i8(stream, self.idealpitch)

        if self.flags & ServerUpdateFlags.PUNCH1:
            bindata.write_i8(stream, self.punchangle[0])
        if self.flags & ServerUpdateFlags.VELOCITY1:
            bindata.write_i8(stream, round(self.velocity[0] / 16.0))
        if self.flags & ServerUpdateFlags.PUNCH2:
            bindata.write_i8(stream, self.punchangle[1])
        if self.flags & ServerUpdateFlags.VELOCITY2:
            bindata.write_i8(stream, round(self.velocity[1] / 16.0))
        if self.flags & ServerUpdateFlags.PUNCH3:
            bindata.write_i8(stream, self.punchangle[2])
        if self.flags & ServerUpdateFlags.VELOCITY3:
            bindata.write_i8(stream, round(self.velocity[2] / 16.0))

        bindata.write_u32(stream, self.items)
        if self.flags & ServerUpdateFlags.WEAPONFRAME:
            bindata.write_u8(stream, self.weaponframe & 0x00ff)
        if self.flags & ServerUpdateFlags.ARMOR:
            bindata.write_u8(stream, self.armor & 0x00ff)
        if self.flags & ServerUpdateFlags.WEAPON:
            bindata.write_u8(stream, self.weapon & 0x00ff)
        bindata.write_i16(stream, self.health)
        bindata.write_u8(stream, self.ammo & 0x00ff)
        bindata.write_u8(stream, self.shells & 0x00ff)
        bindata.write_u8(stream, self.nails & 0x00ff)
        bindata.write_u8(stream, self.rockets & 0x00ff)
        bindata.write_u8(stream, self.cells & 0x00ff)
        bindata.write_u8(stream, self.activeweapon)

        if self.flags & ServerUpdateFlags.WEAPON2:
            bindata.write_u8(stream, self.weapon >> 8)
        if self.flags & ServerUpdateFlags.ARMOR2:
            bindata.write_u8(stream, self.armor >> 8)
        if self.flags & ServerUpdateFlags.AMMO2:
            bindata.write_u8(stream, self.ammo >> 8)
        if self.flags & ServerUpdateFlags.SHELLS2:
            bindata.write_u8(stream, self.shells >> 8)
        if self.flags & ServerUpdateFlags.NAILS2:
            bindata.write_u8(stream, self.nails >> 8)
        if self.flags & ServerUpdateFlags.ROCKETS2:
            bindata.write_u8(stream, self.rockets >> 8)
        if self.flags & ServerUpdateFlags.CELLS2:
            bindata.write_u8(stream, self.cells >> 8)
        if self.flags & ServerUpdateFlags.WEAPONFRAME2:
            bindata.write_u8(stream, self.weaponframe >> 8)

        if self.flags & ServerUpdateFlags.WEAPONALPHA:
            bindata.write_u8(stream, self.weaponalpha)

    @staticmethod
    def parse(stream):
        flags = ServerUpdateFlags(bindata.read_u16(stream))
        if flags & ServerUpdateFlags.EXTEND1:
            flags |= ServerUpdateFlags(bindata.read_u8(stream) << 16)
        if flags & ServerUpdateFlags.EXTEND2:
            flags |= ServerUpdateFlags(bindata.read_u8(stream) << 24)

        viewheight = bindata.read_i8(stream) if (flags & ServerUpdateFlags.VIEWHEIGHT) else ClientDataMessage.DEFAULT_VIEWHEIGHT
        idealpitch = bindata.read_i8(stream) if (flags & ServerUpdateFlags.IDEALPITCH) else 0.0

        punchangle = [0.0, 0.0, 0.0]
        velocity = [0.0, 0.0, 0.0]
        if flags & ServerUpdateFlags.PUNCH1:
            punchangle[0] = bindata.read_i8(stream)
        if flags & ServerUpdateFlags.VELOCITY1:
            velocity[0] = bindata.read_i8(stream) * 16
        if flags & ServerUpdateFlags.PUNCH2:
            punchangle[1] = bindata.read_i8(stream)
        if flags & ServerUpdateFlags.VELOCITY2:
            velocity[1] = bindata.read_i8(stream) * 16
        if flags & ServerUpdateFlags.PUNCH3:
            punchangle[2] = bindata.read_i8(stream)
        if flags & ServerUpdateFlags.VELOCITY3:
            velocity[2] = bindata.read_i8(stream) * 16

        items = ItemFlags(bindata.read_u32(stream))
        weaponframe = bindata.read_u8(stream) if (flags & ServerUpdateFlags.WEAPONFRAME) else 0
        armor = bindata.read_u8(stream) if (flags & ServerUpdateFlags.ARMOR) else 0
        weapon = bindata.read_u8(stream) if (flags & ServerUpdateFlags.WEAPON) else 0
        health = bindata.read_i16(stream)
        ammo = bindata.read_u8(stream)
        shells = bindata.read_u8(stream)
        nails = bindata.read_u8(stream)
        rockets = bindata.read_u8(stream)
        cells = bindata.read_u8(stream)
        activeweapon = ItemFlags(bindata.read_u8(stream))

        if flags & ServerUpdateFlags.WEAPON2:
            weapon += bindata.read_u8(stream) << 8
        if flags & ServerUpdateFlags.ARMOR2:
            armor += bindata.read_u8(stream) << 8
        if flags & ServerUpdateFlags.AMMO2:
            ammo += bindata.read_u8(stream) << 8
        if flags & ServerUpdateFlags.SHELLS2:
            shells += bindata.read_u8(stream) << 8
        if flags & ServerUpdateFlags.NAILS2:
            nails += bindata.read_u8(stream) << 8
        if flags & ServerUpdateFlags.ROCKETS2:
            rockets += bindata.read_u8(stream) << 8
        if flags & ServerUpdateFlags.CELLS2:
            cells += bindata.read_u8(stream) << 8
        if flags & ServerUpdateFlags.WEAPONFRAME2:
            weaponframe += bindata.read_u8(stream) << 8

        weaponalpha = bindata.read_u8(stream) if (flags & ServerUpdateFlags.WEAPONALPHA) else 1

        return ClientDataMessage(flags, viewheight, idealpitch, punchangle,
            velocity, items, weaponframe, armor, weapon, health, ammo, shells,
            nails, rockets, cells, activeweapon, weaponalpha)


@dataclasses.dataclass
class StopSoundMessage:
    ID = 16

    data: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_i16(stream, self.data)

    @staticmethod
    def parse(stream):
        return StopSoundMessage(data=bindata.read_i16(stream))


@dataclasses.dataclass
class UpdateColorsMessage:
    ID = 17

    player_id: int
    color: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.player_id)
        bindata.write_u8(stream, self.color)

    @staticmethod
    def parse(stream):
        return UpdateColorsMessage(player_id=bindata.read_u8(stream),
                                   color=bindata.read_u8(stream))


@dataclasses.dataclass
class ParticleMessage:
    ID = 18

    origin: list[float]
    direction: list[int]
    count: int
    color: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        write_coord_n(protocol_flags, stream, self.origin)
        bindata.write_i8_n(stream, self.direction)
        bindata.write_u8(stream, self.count)
        bindata.write_u8(stream, self.color)

    @staticmethod
    def parse(stream):
        return ParticleMessage(
            origin=read_coord_n(protocol_flags, stream, 3),
            direction=bindata.read_i8_n(stream, 3),
            count=bindata.read_u8(stream), color=bindata.read_u8(stream))


@dataclasses.dataclass
class DamageMessage:
    ID = 19

    armor: int
    blood: int
    from_coords: list[float]

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.armor)
        bindata.write_u8(stream, self.blood % 256)
        write_coord_n(protocol_flags, stream, self.from_coords)

    @staticmethod
    def parse(stream):
        return DamageMessage(
            armor=bindata.read_u8(stream), blood=bindata.read_u8(stream),
            from_coords=read_coord_n(protocol_flags, stream, 3))


@dataclasses.dataclass
class SpawnStaticMessage:
    ID = 20

    modelindex: int
    frame: int
    colormap: int
    skin: int
    origin: list[float]
    angles: list[float]

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.modelindex)
        bindata.write_u8(stream, self.frame)
        bindata.write_u8(stream, self.colormap)
        bindata.write_u8(stream, self.skin)
        write_coord_n(protocol_flags, stream, self.origin)
        write_angle_n(protocol_flags, stream, self.angles)

    @staticmethod
    def parse(stream):
        return SpawnStaticMessage(
            modelindex=bindata.read_u8(stream),
            frame=bindata.read_u8(stream),
            colormap=bindata.read_u8(stream),
            skin=bindata.read_u8(stream),
            origin=read_coord_n(protocol_flags, stream, 3),
            angles=read_angle_n(protocol_flags, stream, 3))


@dataclasses.dataclass
class SpawnBaselineMessage:
    ID = 22

    entity_num: int
    modelindex: int
    frame: int
    colormap: int
    skin: int
    origin: list[float]
    angles: list[float]

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_i16(stream, self.entity_num)
        bindata.write_u8(stream, self.modelindex)
        bindata.write_u8(stream, self.frame)
        bindata.write_u8(stream, self.colormap)
        bindata.write_u8(stream, self.skin)
        for i in range(3):
            write_coord(protocol_flags, stream, self.origin[i])
            write_angle(protocol_flags, stream, self.angles[i])

    @staticmethod
    def parse(stream):
        entity_num = bindata.read_i16(stream)
        modelindex=bindata.read_u8(stream)
        frame = bindata.read_u8(stream)
        colormap = bindata.read_u8(stream)
        skin = bindata.read_u8(stream)
        origin = [None, None, None]
        angles = [None, None, None]
        for i in range(3):
            origin[i] = read_coord(protocol_flags, stream)
            angles[i] = read_angle(protocol_flags, stream)
        return SpawnBaselineMessage(entity_num, modelindex, frame, colormap,
            skin, origin, angles)


class TempEntityType(enum.IntEnum):
    SPIKE = 0
    SUPERSPIKE = 1
    GUNSHOT = 2
    EXPLOSION = 3
    TAREXPLOSION = 4
    LIGHTNING1 = 5
    LIGHTNING2 = 6
    WIZSPIKE = 7
    KNIGHTSPIKE = 8
    LIGHTNING3 = 9
    LAVASPLASH = 10
    TELEPORT = 11
    EXPLOSION2 = 12
    BEAM = 13
    EXPLOSION3 = 16
    LIGHTNING4 = 17

@dataclasses.dataclass
class TempEntityPosition:
    pos: list[float]

    def write(self, stream):
        write_coord_n(protocol_flags, stream, self.pos)

    @staticmethod
    def parse(stream):
        return TempEntityPosition(
            pos=read_coord_n(protocol_flags, stream, 3))

@dataclasses.dataclass
class TempEntityPositionColormap:
    pos: list[float]
    color_start: int
    color_end: int

    def write(self, stream):
        write_coord_n(protocol_flags, stream, self.pos)
        bindata.write_u8(stream, self.color_start)
        bindata.write_u8(stream, self.color_end)

    @staticmethod
    def parse(stream):
        return TempEntityPositionColormap(
            pos=read_coord_n(protocol_flags, stream, 3),
            color_start=bindata.read_u8(stream),
            color_end=bindata.read_u8(stream))

@dataclasses.dataclass
class TempEntityPositionColor:
    pos: list[float]
    color: list[float]

    def write(self, stream):
        write_coord_n(protocol_flags, stream, self.pos)
        write_coord_n(protocol_flags, stream, self.color)

    @staticmethod
    def parse(stream):
        return TempEntityPositionColor(
            pos=read_coord_n(protocol_flags, stream, 3),
            explosion_color=read_coord_n(protocol_flags, stream, 3))

@dataclasses.dataclass
class TempEntityBeam:
    entity_num: int
    start: list[float]
    end: list[float]

    def write(self, stream):
        bindata.write_i16(stream, self.entity_num)
        write_coord_n(protocol_flags, stream, self.start)
        write_coord_n(protocol_flags, stream, self.end)

    @staticmethod
    def parse(stream):
        return TempEntityBeam(entity_num=bindata.read_i16(stream),
                              start=read_coord_n(protocol_flags, stream, 3),
                              end=read_coord_n(protocol_flags, stream, 3))

@dataclasses.dataclass
class TempEntityBeamName:
    name: str
    beam: TempEntityBeam

    def write(self, stream):
        bindata.write_c_str(stream, self.name)
        self.beam.write(stream)

    @staticmethod
    def parse(stream):
        return TempEntityBeamName(name=bindata.read_c_str(stream),
                                  beam=TempEntityBeam.parse(stream))

@dataclasses.dataclass
class TempEntityMessage:
    ID = 23

    type: TempEntityType
    data: None

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.type)
        self.data.write(stream)

    @staticmethod
    def parse(stream):
        type = TempEntityType(bindata.read_u8(stream))
        match type:
            case (TempEntityType.WIZSPIKE |
                  TempEntityType.KNIGHTSPIKE |
                  TempEntityType.SPIKE |
                  TempEntityType.SUPERSPIKE |
                  TempEntityType.GUNSHOT |
                  TempEntityType.EXPLOSION |
                  TempEntityType.TAREXPLOSION |
                  TempEntityType.LAVASPLASH |
                  TempEntityType.TELEPORT):
                return TempEntityMessage(type, TempEntityPosition.parse(stream))
            case TempEntityType.EXPLOSION2:
                return TempEntityMessage(type, TempEntityPositionColormap.parse(stream))
            case TempEntityType.EXPLOSION3:
                return TempEntityMessage(type, TempEntityPositionColor.parse(stream))
            case (TempEntityType.LIGHTNING1 |
                  TempEntityType.LIGHTNING2 |
                  TempEntityType.LIGHTNING3 |
                  TempEntityType.BEAM):
                return TempEntityMessage(type, TempEntityBeam.parse(stream))
            case TempEntityType.LIGHTNING4:
                return TempEntityMessage(type, TempEntityBeamName.parse(stream))
            case _:
                assert False


@dataclasses.dataclass
class SetPauseMessage:
    ID = 24

    paused: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.paused)

    @staticmethod
    def parse(stream):
        return SetPauseMessage(paused=bindata.read_u8(stream))


@dataclasses.dataclass
class SignOnNumMessage:
    ID = 25

    stage: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.stage)

    @staticmethod
    def parse(stream):
        return SignOnNumMessage(stage=bindata.read_u8(stream))


@dataclasses.dataclass
class CenterPrintMessage:
    ID = 26

    text: str

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_c_str(stream, self.text)

    @staticmethod
    def parse(stream):
        return CenterPrintMessage(text=bindata.read_c_str(stream))


@dataclasses.dataclass
class KilledMonsterMessage:
    ID = 27

    def write(self, stream):
        bindata.write_u8(stream, self.ID)

    @staticmethod
    def parse(stream):
        return KilledMonsterMessage()


@dataclasses.dataclass
class FoundSecretMessage:
    ID = 28

    def write(self, stream):
        bindata.write_u8(stream, self.ID)

    @staticmethod
    def parse(stream):
        return FoundSecretMessage()


@dataclasses.dataclass
class SpawnStaticSoundMessage:
    ID = 29

    origin: list[float]
    sound_num: int
    volume: int
    attenuation: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        write_coord_n(protocol_flags, stream, self.origin)
        bindata.write_u8(stream, self.sound_num)
        bindata.write_u8(stream, self.volume)
        bindata.write_u8(stream, self.attenuation)

    @staticmethod
    def parse(stream):
        return SpawnStaticSoundMessage(
            origin=read_coord_n(protocol_flags, stream, 3),
            sound_num=bindata.read_u8(stream), volume=bindata.read_u8(stream),
            attenuation=bindata.read_u8(stream))


@dataclasses.dataclass
class IntermissionMessage:
    ID = 30

    def write(self, stream):
        bindata.write_u8(stream, self.ID)

    @staticmethod
    def parse(stream):
        return IntermissionMessage()


@dataclasses.dataclass
class FinaleMessage:
    ID = 31

    text: str

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_c_str(stream, self.text)

    @staticmethod
    def parse(stream):
        return FinaleMessage(text=bindata.read_c_str(stream))


@dataclasses.dataclass
class CdTrackMessage:
    ID = 32

    cdtrack: int
    looptrack: int

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_u8(stream, self.cdtrack)
        bindata.write_u8(stream, self.looptrack)

    @staticmethod
    def parse(stream):
        return CdTrackMessage(cdtrack=bindata.read_u8(stream),
                              looptrack=bindata.read_u8(stream))


@dataclasses.dataclass
class SellscreenMessage:
    ID = 33

    def write(self, stream):
        bindata.write_u8(stream, self.ID)

    @staticmethod
    def parse(stream):
        return SellscreenMessage()


@dataclasses.dataclass
class CutsceneMessage:
    ID = 34

    text: str

    def write(self, stream):
        bindata.write_u8(stream, self.ID)
        bindata.write_c_str(stream, self.text)

    @staticmethod
    def parse(stream):
        return CutsceneMessage(text=bindata.read_c_str(stream))


MESSAGE_TYPES = [
    BadMessage,
    NopMessage,
    DisconnectMessage,
    UpdateStatMessage,
    VersionMessage,
    SetViewMessage,
    SoundMessage,
    TimeMessage,
    PrintMessage,
    StuffTextMessage,
    SetAngleMessage,
    ServerInfoMessage,
    LightstyleMessage,
    UpdateNameMessage,
    UpdateFragsMessage,
    ClientDataMessage,
    StopSoundMessage,
    UpdateColorsMessage,
    ParticleMessage,
    DamageMessage,
    SpawnStaticMessage,
    SpawnBaselineMessage,
    TempEntityMessage,
    SetPauseMessage,
    SignOnNumMessage,
    CenterPrintMessage,
    KilledMonsterMessage,
    FoundSecretMessage,
    SpawnStaticSoundMessage,
    IntermissionMessage,
    FinaleMessage,
    CdTrackMessage,
    SellscreenMessage,
    CutsceneMessage,
]

MESSAGE_TYPE_FROM_ID = dict(zip([m.ID for m in MESSAGE_TYPES], MESSAGE_TYPES))


# this should be (enum.IntFlag), but that has terrible performance with the
# bitwise and operator. So instead let's use plain int
class UpdateFlags:
    MOREBITS = (1<<0)
    ORIGIN1 = (1<<1)
    ORIGIN2 = (1<<2)
    ORIGIN3 = (1<<3)
    ANGLE2 = (1<<4)
    NOLERP = (1<<5)
    FRAME = (1<<6)
    SIGNAL = (1<<7)
    ANGLE1 = (1<<8)
    ANGLE3 = (1<<9)
    MODEL = (1<<10)
    COLORMAP = (1<<11)
    SKIN = (1<<12)
    EFFECTS = (1<<13)
    LONGENTITY = (1<<14)
    # nehahra support
    TRANS = (1<<15)
    # Protocol.FITZQUAKE
    EXTEND1 = (1<<15)
    ALPHA = (1<<16)
    FRAME2 = (1<<17)
    MODEL2 = (1<<18)
    LERPFINISH = (1<<19)
    SCALE = (1<<20)
    UNUSED21 = (1<<21)
    UNUSED22 = (1<<22)
    EXTEND2 = (1<<23)

@dataclasses.dataclass
class EntityUpdateMessage:
    flags: int
    num: int
    modelindex: int
    frame: int
    colormap: int
    skinnum: int
    effects: int
    origin: list[float]
    angles: list[float]
    temp: float
    transparency: float
    fullbright: float
    alpha: int
    scale: int
    frame_finish_time: int

    def write(self, stream):
        # TODO: Need to adapt this if we change certain data
        bindata.write_u8(stream, self.flags & 0x000000ff)
        if self.flags & UpdateFlags.MOREBITS:
            bindata.write_u8(stream, (self.flags & 0x0000ff00) >> 8)
        if protocol != ProtocolVersion.NETQUAKE:
            if self.flags & UpdateFlags.EXTEND1:
                bindata.write_u8(stream, (self.flags & 0x00ff0000) >> 16)
            if self.flags & UpdateFlags.EXTEND2:
                bindata.write_u8(stream, self.flags >> 24)

        if self.flags & UpdateFlags.LONGENTITY:
            bindata.write_i16(stream, self.num)
        else:
            bindata.write_u8(stream, self.num)
        if self.flags & UpdateFlags.MODEL:
            bindata.write_u8(stream, self.modelindex & 0x00ff)
        if self.flags & UpdateFlags.FRAME:
            bindata.write_u8(stream, self.frame & 0x00ff)
        if self.flags & UpdateFlags.COLORMAP:
            bindata.write_u8(stream, self.colormap)
        if self.flags & UpdateFlags.SKIN:
            bindata.write_u8(stream, self.skinnum)
        if self.flags & UpdateFlags.EFFECTS:
            bindata.write_u8(stream, self.effects)

        if self.flags & UpdateFlags.ORIGIN1:
            write_coord(protocol_flags, stream, self.origin[0])
        if self.flags & UpdateFlags.ANGLE1:
            write_angle(protocol_flags, stream, self.angles[0])
        if self.flags & UpdateFlags.ORIGIN2:
            write_coord(protocol_flags, stream, self.origin[1])
        if self.flags & UpdateFlags.ANGLE2:
            write_angle(protocol_flags, stream, self.angles[1])
        if self.flags & UpdateFlags.ORIGIN3:
            write_coord(protocol_flags, stream, self.origin[2])
        if self.flags & UpdateFlags.ANGLE3:
            write_angle(protocol_flags, stream, self.angles[2])

        if protocol == ProtocolVersion.NETQUAKE:
            if self.flags & UpdateFlags.TRANS:
                bindata.write_f32(stream, self.temp)
                bindata.write_f32(stream, self.transparency)
                if self.temp == 2.0:
                    bindata.write_f32(stream, self.fullbright)
        else:
            if self.flags & UpdateFlags.ALPHA:
                bindata.write_u8(stream, self.alpha)
            if self.flags & UpdateFlags.SCALE:
                bindata.write_u8(stream, self.scale)
            if self.flags & UpdateFlags.FRAME2:
                bindata.write_u8(stream, self.frame >> 8)
            if self.flags & UpdateFlags.MODEL2:
                bindata.write_u8(stream, self.modelindex >> 8)
            if self.flags & UpdateFlags.LERPFINISH:
                bindata.write_u8(stream, self.frame_finish_time)

    @staticmethod
    def parse(flags: int, stream):
        if flags & UpdateFlags.MOREBITS:
            flags |= bindata.read_u8(stream) << 8

        if protocol != ProtocolVersion.NETQUAKE:
            if flags & UpdateFlags.EXTEND1:
                flags |= bindata.read_u8(stream) << 16
            if flags & UpdateFlags.EXTEND2:
                flags |= bindata.read_u8(stream) << 24

        num = bindata.read_i16(stream) if (flags & UpdateFlags.LONGENTITY) else bindata.read_u8(stream)
        modelindex = bindata.read_u8(stream) if (flags & UpdateFlags.MODEL) else None  # TODO: default from baseline
        frame = bindata.read_u8(stream) if (flags & UpdateFlags.FRAME) else None
        colormap = bindata.read_u8(stream) if (flags & UpdateFlags.COLORMAP) else None
        skinnum = bindata.read_u8(stream) if (flags & UpdateFlags.SKIN) else None
        effects = bindata.read_u8(stream) if (flags & UpdateFlags.EFFECTS) else None

        origin = [0, 0, 0]  # TODO: should be from baseline. actually need this for backpack origin
        angles = [None, None, None]
        if flags & UpdateFlags.ORIGIN1:
            origin[0] = read_coord(protocol_flags, stream)
        if flags & UpdateFlags.ANGLE1:
            angles[0] = read_angle(protocol_flags, stream)
        if flags & UpdateFlags.ORIGIN2:
            origin[1] = read_coord(protocol_flags, stream)
        if flags & UpdateFlags.ANGLE2:
            angles[1] = read_angle(protocol_flags, stream)
        if flags & UpdateFlags.ORIGIN3:
            origin[2] = read_coord(protocol_flags, stream)
        if flags & UpdateFlags.ANGLE3:
            angles[2] = read_angle(protocol_flags, stream)

        temp = None
        transparency = None
        fullbright = None
        alpha = None
        scale = None
        frame_finish_time = None
        if protocol == ProtocolVersion.NETQUAKE:
            if flags & UpdateFlags.TRANS:
                temp = bindata.read_f32(stream)
                transparency = bindata.read_f32(stream)
                if temp == 2.0:
                    fullbright = bindata.read_f32(stream)
        else:
            alpha = bindata.read_u8(stream) if (flags & UpdateFlags.ALPHA) else None
            scale = bindata.read_u8(stream) if (flags & UpdateFlags.SCALE) else None
            if flags & UpdateFlags.FRAME2:
                frame += bindata.read_u8(stream) << 8
            if flags & UpdateFlags.MODEL2:
                modelindex += bindata.read_u8(stream) << 8
            frame_finish_time = bindata.read_u8(stream) if (flags & UpdateFlags.LERPFINISH) else None

        return EntityUpdateMessage(flags, num, modelindex, frame, colormap,
            skinnum, effects, origin, angles, temp, transparency, fullbright,
            alpha, scale, frame_finish_time)


def parse_message(stream):
    message_id = bindata.read_u8(stream)
    #if message_id == 0xff:
    #    raise ValueError("end of message")
    if message_id & UpdateFlags.SIGNAL:
        return EntityUpdateMessage.parse(message_id, stream)

    Message = MESSAGE_TYPE_FROM_ID[message_id]
    return Message.parse(stream)
