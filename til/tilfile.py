import zlib
import io
import sys
from til import datatypes as dt
from til.utils import *


class TypeString:
    """Representation of `qtype`."""
    def __init__(self, data, parent=None):
        self._pos = 0
        self._typestring = data
        self._parent = parent

    def __getitem__(self, x):
        """Index/slice typestring"""
        if isinstance(x, slice):
            if x.step is not None:
                raise NotImplementedError(
                    "Typestring slice does not handle stepping")
            if x.stop is None:
                return self._typestring[self._pos + x.start:]
            else:
                return self._typestring[self._pos + x.start:self._pos + x.stop]
        return self._typestring[self._pos + x]

    def __len__(self):
        """Get the length of the typestring"""
        return len(self._typestring)

    def __iadd__(self, n):
        """Increment stream position"""
        self._pos += n
        return self

    def pos(self):
        return self._pos

    def peek(self, n, pos=0):
        return self[pos:pos+n]

    def read(self, n, pos=0):
        data = self[pos:pos+n]
        self.seek(n)
        return data

    def seek(self, n):
        """ ptr+=n """
        self._pos += n
        if self._parent is not None:
            self._parent.seek(n)

    def get(self):
        """ ptr_copy = ptr """
        return TypeString(self[0:])

    def ref(self):
        """ ptr_ref = &ptr """
        return TypeString(self[0:], parent=self)

    def peek_db(self, pos=0):
        """ u8 val = *(u8*)ptr """
        return self[pos]

    def read_db(self, pos=0):
        """ u8 val = *(u8*)ptr++"""
        data = self[pos]
        self.seek(1)
        return data

    def read_dt(self):
        """ Reads 1 to 2 bytes.

        Value Range: 0-0xFFFE
        Usage: 16bit numbers
        :return: int
        """
        val = self.read_db()
        if val & 0x80:
            val = (val & 0x7f | self.read_db() << 7)
        return val - 1

    def read_de(self):
        """ Reads 1 to 5 bytes

        Value Range: 0-0xFFFFFFFF
        Usage: Enum Deltas
        :return: int
        """
        val = 0
        while True:
            b = self.read_db()
            hi = val << 6
            sign = (b & 0x80)
            if not sign:
                lo = b & 0x3f
            else:
                lo = 2 * hi
                hi = b & 0x7f
            val = lo | hi
            if not sign:
                break
        return to_s32(val)

    def read_da(self):
        """ Reads 1 to 9 bytes.

        ValueRange: 0x-0x7FFFFFFF, 0-0xFFFFFFFF
        Usage: Arrays
        :return: (int, int)
        """
        a = 0
        b = 0
        da = 0
        base = 0
        nelem = 0
        while True:
            typ = self.peek_db()
            if typ & 0x80 == 0:
                break
            self.seek(1)
            da = (da << 7) | typ & 0x7f
            if b >= 4:
                z = self.peek_db()
                if z != 0:
                    base = 0x10 * da | z & 0xf
                nelem = (self.read_db() >> 4) & 7
                while True:
                    y = self.peek_db()
                    if (y & 0x80) == 0:
                        break
                    self.seek(1)
                    nelem = (nelem << 7) | y & 0x7f
                    a += 1
                    if a >= 4:
                        return True, nelem, base
        return False, nelem, base

    def read_complex_n(self):
        n = self.read_dt()
        if n == 0x7FFE:
            n = self.read_de()
        return n

    def read_pstring(self):
        length = self.read_dt()
        return self.read(length).decode("ascii")

    def is_tah_byte(self):
        return self.peek_db() == dt.TAH_BYTE

    def is_sdacl_byte(self):
        return ((self.peek_db() & ~dt.TYPE_FLAGS_MASK)
                ^ dt.TYPE_MODIF_MASK) <= dt.BT_VOID

    def parse_type_attr(self):
        tah = self.read_db()
        tmp = ((tah & 1) | ((tah >> 3) & 6)) + 1
        res = 0
        if tah == dt.TAH_BYTE or tmp == 8:
            if tmp == 8:
                res = tmp
            next_byte = self.read_db()
            shift = 0
            while True:
                res |= (next_byte & 0x7f) << shift
                if next_byte & 0x80 == 0:
                    break
                shift += 7
                next_byte = self.read_db()
                if next_byte == 0:
                    raise ValueError("parse_type_attr(): failed to parse")
        if res & dt.TAH_HASATTRS:
            val = self.read_dt()
            for _ in range(val):
                self.read_pstring()
                self.read_pstring()

    def read_type_attr(self):
        if self.is_tah_byte():
            return self.parse_type_attr()

    def read_sdacl_attr(self):
        if self.is_sdacl_byte():
            return self.read_type_attr()


    @staticmethod
    def read_typestring(stream):
        typestring = bytearray()
        while True:
            b = stream.read(1)
            typestring += b
            if b == b'\0':
                break
        return TypeString(typestring)


class PStringList:
    """List of pascal-like strings.

    p_string: dt length, db characters
    p_list: one or more p_strings

    Args:
        data (bytes): null terminated p_list bytes
    """
    def __init__(self, data):
        self._pos = 0
        self._data = data

    def seek(self, n):
        """ ptr+=n """
        self._pos += n
        if self._parent is not None:
            self._parent.seek(n)

    def read(self, n, pos=0):
        data = self[pos:pos+n]
        self.seek(n)
        return data

    # TODO: Replace with read_db
    def read_db(self, pos=0):
        """ u8 val = *(u8*)ptr++"""
        data = self[pos]
        self.seek(1)
        return data

    def read_dt(self):
        """ Reads 1 to 2 bytes.

        Value Range: 0-0xFFFE
        Usage: 16bit numbers
        :return: int
        """
        val = self.read_db()
        if val & 0x80:
            val = (val & 0x7f | self.read_db() << 7)
        return val - 1

    def read_pstring(self):
        length = self.read_dt()
        return self.read(length).decode("ascii")

    @staticmethod
    def read_p_list(stream):
        p_list = bytearray()
        while True:
            b = stream.read(1)
            p_list += b
            if b == b'\0':
                break
        return PStringList(bytes(p_list))


class TypeInfo:
    """Representation of tinfo_t."""
    def __init__(self, base_type=dt.BT_UNK):
        self._base_type = base_type
        self._flags = 0
        self._typedetails = 0

    def base_type(self):
        return self._base_type

    def typedetails(self):
        return self._typedetails

    @staticmethod
    def create_type_info(base, details=None):
        tinfo = TypeInfo(base)
        tinfo._typedetails = details
        return tinfo


class TypeData:
    """Represents the serialized type data"""
    def __init__(self, stream):
        self._stream = stream
        self._type = 0              # BT_UNK
        self._tinfo = None      # Should be filled in by deserialize
        self._read()

    def _read(self):
        self._flags = u32(self._stream)
        self._name = cstring(self._stream)
        # For symbols, this is the value
        self._ordinal = u64(self._stream) if self._flags >> 32 \
            else u32(self._stream)

        self._typestr = TypeString.read_typestring(self._stream)
        self._cmt = cstring(self._stream)
        self._fields = self._parse_plist()
        self._fieldcmts = self._parse_plist()
        self._sclass = u8(self._stream)

    def __repr__(self):
        return self.name()

    def name(self):
        return self._name.decode("ascii")

    def ordinal(self):
        return self._ordinal

    def typestring(self):
        return self._typestr

    def fields(self):
        return self._fields

    def fieldcmts(self):
        return self._fieldcmts

    def comment(self):
        return self._cmt

    def set_type_info(self, tinfo):
        self._tinfo = tinfo

    def get_type_info(self):
        return self._tinfo

    def _parse_plist(self):
        p_list = []
        length = u8(self._stream)
        while length != 0:
            p_list.append(self._stream.read(length - 1).decode("ascii"))
            length = u8(self._stream)
        return p_list


class Macro:
    """Represents a macro loaded from a bucket.

    TODO: Should probably be merged with TypeData.
    """
    def __init__(self, stream):
        self._name = cstring(stream)
        self._nparams = u8(stream)
        self._isfunc = u8(stream)
        self._value = cstring(stream)

    def name(self):
        return self._name.decode("ascii")


class TILBucket:
    """Handle's unpacking a single TIL bucket."""
    def __init__(self, flags, stream):
        self.types = []
        self.ndefs = u32(stream)    # Number of definitions
        self.size = u32(stream)     # Size of uncompressed buffer
        self.buffer = None          # Buffer
        if flags & 0x1:
            csize = u32(stream)
            self.buffer = zlib.decompress(stream.read(csize))
        else:
            self.buffer = stream.read(self.size)

    def add_type(self, t):
        self.types.append(t)

    def get_types(self):
        return self.types


# TIL values for `flags`
TIL_ZIP = 0x0001
TIL_MAC = 0x0002
TIL_ESI = 0x0004
TIL_UNI = 0x0008
TIL_ORD = 0x0010
TIL_ALI = 0x0020
TIL_MOD = 0x0040
TIL_STM = 0x0080
TIL_SLD = 0x0100


class TILHeader:
    """Parses the TIL header."""
    def __init__(self, stream):
        self._stream = stream
        self._read()

    def _read(self):
        self.sig = self._stream.read(6)
        self.form = u32(self._stream)
        self.flag = u32(self._stream)
        self.titlelen = u8(self._stream)
        self.title = self._stream.read(self.titlelen)
        self.baselen = u8(self._stream)
        self.base = self._stream.read(self.baselen)
        self.id = u8(self._stream)
        self.cm = u8(self._stream)
        self.size_i = u8(self._stream)
        self.size_b = u8(self._stream)
        self.size_e = u8(self._stream)
        self.defalign = u8(self._stream)
        if self.flag & 0x4:
            self.size_s = u8(self._stream)
            self.size_l = u8(self._stream)
            self.size_ll = u8(self._stream)
        if self.flag & 0x100:
            self.size_ldbl = u8(self._stream)


class TIL:
    """Represents a single TIL file."""
    def __init__(self, stream):
        self._stream = stream
        self._header = None
        self._typeinfos = []
        self._read_header()
        self._read_buckets()

    def _read_header(self):
        """Read the TIL header."""
        self._stream.seek(0)
        self._header = TILHeader(self._stream)

    def _read_buckets(self):
        """Read each bucket."""
        self._syms = self._read_bucket()
        self._types = self._read_bucket()
        self._macros = self._read_bucket()
        self._load_bucket(self._syms)
        self._load_bucket(self._types)
        self._load_macros(self._macros)
        self._process_bucket(self._syms)
        self._process_bucket(self._types)

    def _read_bucket(self):
        """Read a single bucket."""
        return TILBucket(self._header.flag, self._stream)

    def _read_type(self, stream):
        return TypeData(stream)

    def _read_macro(self, stream):
        return Macro(stream)

    def _load_bucket(self, bucket):
        buffer = io.BytesIO(bucket.buffer)
        for _ in range(bucket.ndefs):
            bucket.add_type(self._read_type(buffer))

    def _load_macros(self, bucket):
        buffer = io.BytesIO(bucket.buffer)
        for _ in range(bucket.ndefs):
            bucket.add_type(self._read_macro(buffer))

    def _process_bucket(self, bucket):
        self._deserialize_bucket(bucket)

    def _deserialize_bucket(self, bucket):
        for tdata in bucket.get_types():
            #print(f"Deserializing {tdata.name()}")
            tinfo = self.deserialize(tdata.typestring(),
                                     tdata.fields(),
                                     tdata.fieldcmts())
            if tinfo is not None:
                self._typeinfos.append(tinfo)
                tdata.set_type_info(tinfo)

    def deserialize(self, typestr, fields, fieldcmts):
        typ = typestr.peek_db()
        base = typ & dt.TYPE_BASE_MASK
        flags = typ & dt.TYPE_FLAGS_MASK
        mod = typ & dt.TYPE_MODIF_MASK

        if base <= dt.BT_LAST_BASIC:
            typestr.seek(1)
            return TypeInfo(typ)

        if base > dt.BT_LAST_BASIC:
            typedata = None
            if base == dt.BT_COMPLEX and flags != dt.BTMT_TYPEDEF:
                t = typestr.get()
                t.seek(1)
                N = t.read_complex_n()
                if N == 0:
                    typedata = dt.TypedefTypeData()
                    typedata.name = t.read_pstring()
                    # I don't like this, we're going to need to come up with a
                    # way to do this automatically
                    typestr.seek(t.pos())
                    return TypeInfo.create_type_info(typ, typedata)

            if base == dt.BT_PTR:
                typedata = dt.PointerTypeData() \
                    .deserialize(self, typestr, fields, fieldcmts)
            elif base == dt.BT_ARRAY:
                typedata = dt.ArrayTypeData() \
                    .deserialize(self, typestr, fields, fieldcmts)
            elif base == dt.BT_FUNC:
                typedata = dt.FuncTypeData() \
                    .deserialize(self, typestr, fields, fieldcmts)
            elif base == dt.BT_COMPLEX:
                if flags == dt.BTMT_STRUCT or flags == dt.BTMT_UNION:
                    typedata = dt.UdtTypeData() \
                        .deserialize(self, typestr, fields, fieldcmts)
                elif flags == dt.BTMT_ENUM:
                    typedata = dt.EnumTypeData() \
                        .deserialize(self, typestr, fields, fieldcmts)
                elif flags == dt.BTMT_TYPEDEF:
                    typedata = dt.TypedefTypeData() \
                        .deserialize(self, typestr, fields, fieldcmts)
            elif base == dt.BT_BITFIELD:
                typedata = dt.BitfieldTypeData() \
                    .deserialize(self, typestr, fields, fieldcmts)
            return TypeInfo.create_type_info(typ, typedata)

    def header(self):
        return self._header

    def syms(self):
        return self._syms

    def types(self):
        return self._types

    def macros(self):
        return self._macros

    def get_named_type(self, name, is_type):
        """

        Args:
            name: The name of the type
            is_type: True if this is a type and otherwise for symbols

        Returns: TypeData for the type
        """
        bucket = self._types if is_type else self._syms
        for typ in bucket.get_types():
            if name == typ.name():
                return typ

    def get_enums(self):
        enums = []
        for tdata in self._types.get_types():
            tinfo = tdata.get_type_info()
            typ = tinfo.base_type()
            base = typ & dt.TYPE_BASE_MASK
            flags = typ & dt.TYPE_FLAGS_MASK
            if base == dt.BT_COMPLEX and flags == dt.BTMT_ENUM:
                enums.append(tdata)
        return enums

    def get_structs(self):
        enums = []
        for tdata in self._types.get_types():
            tinfo = tdata.get_type_info()
            typ = tinfo.base_type()
            base = typ & dt.TYPE_BASE_MASK
            flags = typ & dt.TYPE_FLAGS_MASK
            if base == dt.BT_COMPLEX and flags == dt.BTMT_STRUCT:
                enums.append(tdata)
        return enums


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage {sys.argv[0]} <til file>")
        exit()
    with open(sys.argv[1], "rb") as fp, open("log.txt", "w") as log:
        til = TIL(fp)
        for enum in til.get_enums():
            details = enum.get_type_info().typedetails()
            details.print(enum.name())
        for struct in til.get_structs():
            details = struct.get_type_info().typedetails()
            details.print(struct.name())
