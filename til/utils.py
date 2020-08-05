import struct


def u8(stream):
    return struct.unpack("<B", stream.read(1))[0]


def u16(stream):
    return struct.unpack("<H", stream.read(2))[0]


def u32(stream):
    return struct.unpack("<I", stream.read(4))[0]


def u64(stream):
    return struct.unpack("<Q", stream.read(8))[0]


def to_s32(n):
    n = n & 0xffffffff
    return n | (-(n & 0x80000000))


def cstring(stream):
    s = bytearray()
    while True:
        b = stream.read(1)
        if b == b'\0':
            return s
        s += b

