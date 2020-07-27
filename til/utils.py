

def u8(stream):
    return int.from_bytes(stream.read(1), byteorder='little')


def u16(stream):
    return int.from_bytes(stream.read(2), byteorder='little')


def u32(stream):
    return int.from_bytes(stream.read(4), byteorder='little')


def u64(stream):
    return int.from_bytes(stream.read(8), byteorder='little')


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

