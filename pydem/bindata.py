import struct

def read_bytes(stream, num) -> bytes:
    data = stream.read(num)
    if len(data) != num:
        raise ValueError('error reading!')
    return data

def unpack_bytes(format, bytes):
    value = struct.unpack(format, bytes)
    if len(value) != 1:
        raise ValueError('error unpacking!')
    return value[0]

def write_str(stream, value: bytes):
    stream.write(value)

def read_char(stream) -> bytes:
    return read_bytes(stream, 1)

def read_c_str(stream) -> bytes:
    ret = b''
    character = read_char(stream)
    while character != b'\0':
        ret += character
        character = read_char(stream)
    return ret

def write_c_str(stream, value: bytes):
    write_str(stream, value)
    stream.write(b'\0')

def write_f32(stream, value: float):
    stream.write(struct.pack('f', value))

def write_f32_n(stream, values: list[float]):
    for value in values:
        stream.write(struct.pack('f', value))

def read_f32(stream) -> float:
    return unpack_bytes('f', read_bytes(stream, 4))

def read_f32_n(stream, n: int) -> list[float]:
    return [read_f32(stream) for _ in range(n)]

def read_i8(stream) -> int:
    return unpack_bytes('b', read_bytes(stream, 1))

def write_i8(stream, value: int):
    stream.write(struct.pack('b', value))

def write_i8_n(stream, values: list[int]):
    for value in values:
        write_i8(stream, value)

def read_i8_n(stream, n: int) -> list[int]:
    return [read_i8(stream) for _ in range(n)]

def read_u8(stream) -> int:
    return unpack_bytes('B', read_bytes(stream, 1))

def write_u8(stream, value: int):
    stream.write(struct.pack('B', value))

def read_i16(stream) -> int:
    return unpack_bytes('h', read_bytes(stream, 2))

def write_i16(stream, value: int):
    stream.write(struct.pack('h', value))

def read_u16(stream) -> int:
    return unpack_bytes('H', read_bytes(stream, 2))

def write_u16(stream, value: int):
    stream.write(struct.pack('H', value))

def read_i32(stream) -> int:
    return unpack_bytes('i', read_bytes(stream, 4))

def write_i32(stream, value: int):
    stream.write(struct.pack('i', value))

def read_u32(stream) -> int:
    return unpack_bytes('I', read_bytes(stream, 4))

def write_u32(stream, value: int):
    stream.write(struct.pack('I', value))

def write_bytes(stream, data: bytes):
    stream.write(data)
