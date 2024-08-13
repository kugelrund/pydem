import dataclasses
import io

import numpy

from . import bindata
from . import messages
from .messages import Protocol, ProtocolOverride, ProtocolVersion, ProtocolFlags


@dataclasses.dataclass
class CdTrack:
    MAX_CDTRACK_LEN = 12
    cdtrack: str

    def write(self, stream):
        bindata.write_str(stream, self.cdtrack)

    @staticmethod
    def parse(stream):
        string = b''
        for _ in range(CdTrack.MAX_CDTRACK_LEN):
            c = bindata.read_char(stream)
            string += c
            if c == b'\n':
                return CdTrack(string)
        raise ValueError("Error parsing cd track")


@dataclasses.dataclass
class ViewAngles:
    pitch: float
    yaw: float
    roll: float

    def write(self, stream):
        bindata.write_f32_n(stream, (self.pitch, self.yaw, self.roll))

    @staticmethod
    def parse(stream):
        pitch, yaw, roll = bindata.read_f32_n(stream, 3)
        return ViewAngles(pitch, yaw, roll)


@dataclasses.dataclass
class Block:
    viewangles: ViewAngles
    messages: list

    def write(self, stream, protocol: Protocol):
        temp = io.BytesIO()
        for message in self.messages:
            message.write(temp, protocol)
        if not self.messages:
            # block without messages does not seem supported, so write a nop
            messages.NopMessage().write(temp, protocol)
        block_len = temp.tell()

        bindata.write_i32(stream, block_len)
        self.viewangles.write(stream)
        bindata.write_bytes(stream, temp.getbuffer())

    @staticmethod
    def parse(stream, protocol: Protocol):
        block_len = bindata.read_i32(stream)
        viewangles = ViewAngles.parse(stream)

        read_messages = []
        total_num_bytes_read = 0
        while total_num_bytes_read < block_len:
            pos_before = stream.tell()
            message = messages.parse_message(stream, protocol)
            read_messages.append(message)
            total_num_bytes_read += (stream.tell() - pos_before)
        if total_num_bytes_read != block_len:
            raise ValueError(f"Error parsing messages. Read: {total_num_bytes_read}. Expected: {block_len}.")
        return Block(viewangles, read_messages)


@dataclasses.dataclass
class ClientStats:
    items: messages.ItemFlags
    health: int
    armor: int
    shells: int
    nails: int
    rockets: int
    cells: int
    activeweapon: int
    ammo: int
    weaponmodel: int
    weaponframe: int

@dataclasses.dataclass
class Demo:
    cdtrack: CdTrack
    blocks: list[Block]

    def write(self, stream, protocol_override: Protocol = None):
        # assume plain netquake protocol by default (may be changed by
        # ServerInfoMessage during writing of blocks)
        protocol = Protocol(ProtocolVersion.NETQUAKE)
        if protocol_override is not None:
            protocol = ProtocolOverride(protocol_override)
        self.cdtrack.write(stream)
        for block in self.blocks:
            block.write(stream, protocol)

    @staticmethod
    def parse(stream):
        cdtrack = CdTrack.parse(stream)
        blocks = []
        # assume plain netquake protocol by default (may be changed by
        # ServerInfoMessage during parsing of blocks)
        protocol = Protocol(ProtocolVersion.NETQUAKE)
        while stream.read(1):
            stream.seek(-1, 1)
            blocks.append(Block.parse(stream, protocol))
        return Demo(cdtrack, blocks)

    def get_precaches(self):
        server_info_message = [m for b in self.blocks for m in b.messages
                            if isinstance(m, messages.ServerInfoMessage)]
        assert len(server_info_message) == 1
        return (server_info_message[0].models_precache,
                server_info_message[0].sounds_precache)

    def get_yaw(self):
        yaw = numpy.array([block.viewangles.yaw for block in self.blocks])
        for i in range(1, len(yaw)):
            if abs((yaw[i] + 360.0) - yaw[i-1]) < abs(yaw[i] - yaw[i-1]):
                yaw[i:] = yaw[i:] + 360.0
            elif abs((yaw[i] - 360.0) - yaw[i-1]) < abs(yaw[i] - yaw[i-1]):
                yaw[i:] = yaw[i:] - 360.0
        return yaw

    def get_pitch(self):
        return numpy.array([block.viewangles.pitch for block in self.blocks])

    def get_time(self):
        previous_time = 0.0
        times = numpy.zeros(len(self.blocks))
        for i, block in enumerate(self.blocks):
            new_times = [message.time for message in block.messages
                         if isinstance(message, messages.TimeMessage)]
            if new_times:
                assert len(new_times) == 1
                times[i] = new_times[0]
                previous_time = times[i]
            else:
                times[i] = previous_time
        return times

    def get_previous_block_index_with_time_message(self, block_index):
        offsets = (i for i, block in enumerate(reversed(self.blocks[:block_index]))
                   if any(isinstance(m, messages.TimeMessage) for m in block.messages))
        return block_index - 1 - next(offsets, 0)

    def get_fixangle_indices(self):
        indices = []
        for i, block in enumerate(self.blocks):
            for message in block.messages:
                if isinstance(message, messages.SetAngleMessage):
                    indices.append(i)
                    break
        return indices

    def get_client_stats(self):
        client_stats = []
        for block in self.blocks:
            clientdata_messages = [message for message in block.messages
                                   if isinstance(message, messages.ClientDataMessage)]
            if clientdata_messages:
                assert len(clientdata_messages) == 1
                client_stats.append(ClientStats(
                    clientdata_messages[0].items,
                    clientdata_messages[0].health,
                    clientdata_messages[0].armor,
                    clientdata_messages[0].shells,
                    clientdata_messages[0].nails,
                    clientdata_messages[0].rockets,
                    clientdata_messages[0].cells,
                    clientdata_messages[0].activeweapon,
                    clientdata_messages[0].ammo,
                    clientdata_messages[0].weapon,
                    clientdata_messages[0].weaponframe
                    ))
            else:
                client_stats.append(None)
        return client_stats

    def get_final_client_stats(self):
        return next(s for s in reversed(self.get_client_stats()) if s)

    def set_client_stats(self, client_stats_list):
        for block, client_stats in zip(self.blocks, client_stats_list):
            for m in block.messages:
                if not isinstance(m, messages.ClientDataMessage):
                    continue
                m.items = client_stats.items
                m.health = client_stats.health
                m.armor = client_stats.armor
                m.shells = client_stats.shells
                m.nails = client_stats.nails
                m.rockets = client_stats.rockets
                m.cells = client_stats.cells
                m.activeweapon = client_stats.activeweapon
                m.ammo = client_stats.ammo
                m.weapon = client_stats.weaponmodel
                m.weaponframe = client_stats.weaponframe

    def set_yaw(self, yaw):
        for i, block in enumerate(self.blocks):
            block.viewangles.yaw = yaw[i]

    def set_pitch(self, pitch):
        for i, block in enumerate(self.blocks):
            block.viewangles.pitch = pitch[i]
