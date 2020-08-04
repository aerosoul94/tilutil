import zlib
import io
from til.utils import *
from til.datatypes import *


class TypeString:
    """Representation of `qtype`."""
    def __init__(self, data=None, pos=0):
        if data is None:
            data = bytearray()
        self._offset = pos
        self._pos = pos
        self._typestring = data

    def __getitem__(self, x):
        """Index/slice typestring"""
        if isinstance(x, slice):
            if x.step is not None:
                raise NotImplementedError(
                    "Type string slice does not handle stepping")
            if x.stop is None:
                return self._typestring[self._pos + x.start:]
            else:
                return self._typestring[self._pos + x.start:self._pos + x.stop]
        return self._typestring[self._pos + x]

    def __len__(self):
        """Get the length of the typestring"""
        return len(self._typestring) - self._offset

    def __iadd__(self, n):
        """Increment stream position"""
        self._pos += n
        return self

    def data(self):
        return self._typestring

    def pos(self):
        return self._pos - self._offset

    def peek(self, n, pos=0):
        return self[pos:pos+n]

    def read(self, n, pos=0):
        data = self[pos:pos+n]
        self.seek(n)
        return data

    def append(self, data):
        self._typestring += data

    def seek(self, n):
        """ ptr+=n """
        self._pos += n

    def get(self):
        """ ptr_copy = ptr """
        return TypeString(self._typestring, self._pos)

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
        Returns:
            int: Arbitrary value.
        """
        val = self.read_db()
        if val & 0x80:
            val = ((val & 0x7f) | (self.read_db() << 7))
        return val - 1

    def read_de(self):
        """ Reads 1 to 5 bytes

        Value Range: 0-0xFFFFFFFF
        Usage: Enum Deltas
        Returns:
            int: Delta value
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
        return val

    def read_da(self):
        """ Reads 1 to 9 bytes.

        ValueRange: 0x-0x7FFFFFFF, 0-0xFFFFFFFF
        Usage: Arrays
        Returns:
            (int, int): Number of elements and base.
        """
        a = 0
        b = 0
        da = 0
        base = 0
        nelem = 0
        while True:
            c = self.peek_db()
            if c & 0x80 == 0:
                break
            self.seek(1)
            da = (da << 7) | c & 0x7f
            b += 1
            if b >= 4:
                z = self.peek_db()
                if z != 0:
                    base = 0x10 * da | z & 0xf
                nelem = (self.read_db() >> 4) & 7
                while True:
                    c = self.peek_db()
                    if (c & 0x80) == 0:
                        break
                    self.seek(1)
                    nelem = (nelem << 7) | c & 0x7f
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
        return self.read(length)

    def append_db(self, n):
        self._typestring.append(n)

    def append_dt(self, n):
        if n > 0x7ffe:
            raise ValueError("Value too high for append_dt")
        lo = n + 1
        hi = n + 1
        if lo > 127:
            self.append_db(lo & 0x7f | 0x80)
            hi = (lo >> 7) & 0xff
        self.append_db(hi)

    def append_de(self, n):
        buf = bytearray()
        if n & 0xf8000000:
            buf.append(((n >> 0x1b) & 0x7f) | 0x80)
            buf.append(((n >> 0x14) & 0x7f) | 0x80)
            buf.append(((n >> 0xd) & 0x7f) | 0x80)
            buf.append(((n >> 0x6) & 0x7f) | 0x80)
        elif n & 0x7f00000:
            buf.append(((n >> 0x14) & 0x7f) | 0x80)
            buf.append(((n >> 0xd) & 0x7f) | 0x80)
            buf.append(((n >> 0x6) & 0x7f) | 0x80)
        elif n & 0xfe000:
            buf.append(((n >> 0xd) & 0x7f) | 0x80)
            buf.append(((n >> 0x6) & 0x7f) | 0x80)
        elif n & 0x1fc0:
            buf.append(((n >> 6) & 0x7f) | 0x80)
        buf.append((n & 0x3f) | 0x40)
        self.append(buf)

    def append_da(self, n1, n2):
        buf = bytearray()
        # Stores 32 bits for n2 and 31 bits for n1
        buf.append(((n2 >> 0x19) & 0x7f) | 0x80)
        buf.append(((n2 >> 0x12) & 0x7f) | 0x80)
        buf.append(((n2 >> 0xb) & 0x7f) | 0x80)
        buf.append(((n2 >> 0x4) & 0x7f) | 0x80)
        buf.append(((n1 >> 0x18) & 0x70) | ((n2 >> 0) & 0x0f) | 0x80)
        buf.append(((n1 >> 0x15) & 0x7f) | 0x80)
        buf.append(((n1 >> 0xe) & 0x7f) | 0x80)
        buf.append(((n1 >> 0x7) & 0x7f) | 0x80)
        buf.append((n1 & 0x7f) | 0x80)
        self._typestring += buf

    def append_complex_n(self, n, is_empty):
        if n < 0x7ffe and is_empty is False:
            self.append_dt(n)
        else:
            self.append_db(0xff)
            self.append_db(0xff)
            self.append_de(n)

    def append_pstring(self, string):
        self.append_dt(len(string))
        self.append(string.encode("ascii"))

    def is_tah_byte(self):
        return self.peek_db() == TAH_BYTE

    def is_sdacl_byte(self):
        return ((self.peek_db() & ~TYPE_FLAGS_MASK)
                ^ TYPE_MODIF_MASK) <= BT_VOID

    def parse_type_attr(self):
        tah = self.read_db()
        tmp = ((tah & 1) | ((tah >> 3) & 6)) + 1
        res = 0
        if tah == TAH_BYTE or tmp == 8:
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
        if res & TAH_HASATTRS:
            # deserialize type_attrs_t
            val = self.read_dt()
            for _ in range(val):
                key = self.read_pstring()
                val = self.read_pstring()
        return res

    def read_type_attr(self):
        if self.is_tah_byte():
            return self.parse_type_attr()

    def read_sdacl_attr(self):
        if self.is_sdacl_byte():
            return self.parse_type_attr()

    @staticmethod
    def read_typestring(stream):
        typestring = bytearray()
        while True:
            b = stream.read(1)
            typestring += b
            if b == b'\0':
                break
        return TypeString(typestring)


class TypeInfo:
    """Representation of tinfo_t."""
    def __init__(self, base_type=BT_UNK):
        self._type = base_type
        self._flags = 0
        # TODO: Should create a new class TypeDetails to store missing info
        self._typedetails = None

    def get_decl_type(self):
        return self._type

    def get_base_type(self):
        return self._type & TYPE_BASE_MASK

    def get_type_flags(self):
        return self._type & TYPE_FLAGS_MASK

    def get_full_type(self):
        return self._type & TYPE_FULL_MASK

    def get_type_details(self):
        return self._typedetails

    def is_ptr(self):
        return self.get_base_type() == BT_PTR

    def is_array(self):
        return self.get_base_type() == BT_ARRAY

    def is_func(self):
        return self.get_base_type() == BT_FUNC

    def is_bitfield(self):
        return self.get_base_type() == BT_BITFIELD

    def print(self, name):
        if self._typedetails:
            datatype = self._typedetails.print(name)
            if datatype is None:
                print(f"{name} is None")
            return f"{datatype};\n"
        #
        # datatype = print_type(self, name)
        # return f"{datatype} {name};\n"

    @staticmethod
    def create_type_info(base, details=None):
        tinfo = TypeInfo(base)
        tinfo._typedetails = details
        return tinfo


class TypeData:
    """Represents the serialized type data."""
    def __init__(self, stream, format):
        self._stream = stream
        self._type = 0              # BT_UNK
        self._tinfo = None      # Should be filled in by deserialize
        self._read(format)

    def _read(self, format):
        self._flags = u32(self._stream)
        self._name = cstring(self._stream)
        if self._flags not in (0x7fffffff, 0xffffffff):
            raise ValueError("Invalid flags")

        # Format below 0x12 does not have 64 bit ordinal's
        if format < 0x12:
            self._flags &= 0x7fffffff

        # For symbols, this is the value
        self._ordinal = u64(self._stream) if bool(self._flags >> 31) \
            else u32(self._stream)

        self._typestr = TypeString.read_typestring(self._stream)
        self._cmt = cstring(self._stream)
        self._fields = TypeString.read_typestring(self._stream)
        self._fieldcmts = TypeString.read_typestring(self._stream)
        self._sclass = u8(self._stream)

    def __repr__(self):
        return self.get_name()

    def get_name(self):
        """ Get the name for this type.

        Returns:
            str: Type name.
        """
        return self._name.decode("ascii")

    def get_ordinal(self):
        """ Get the type's ordinal/value.

        Returns:
            int: Ordinal or value for symbols.
        """
        return self._ordinal

    def get_type_string(self):
        """ Get the serialized type info string.

        Returns:
            TypeString: Serialized type info string.
        """
        return self._typestr

    def get_fields(self):
        """ Get the serialized field name p-list.

        Returns:
            TypeString: Serialized field names.
        """
        return self._fields

    def get_field_comments(self):
        """ Get the serialized field comments p-list.

        Returns:
            TypeString: Serialized field comments.
        """
        return self._fieldcmts

    def get_comment(self):
        """ Get the serialized comment p-list.

        Returns:
            TypeString: Serialized comments.
        """
        return self._cmt

    def set_type_info(self, tinfo):
        """ Set TypeInfo object.

        Args:
            tinfo (TypeInfo): Input type info object.
        """
        self._tinfo = tinfo

    def get_type_info(self):
        """ Get TypeInfo object.

        Returns:
            TypeInfo: Type info object.
        """
        return self._tinfo


class Macro:
    """Represents a macro loaded from a bucket.

    TODO: Should probably be merged with TypeData.
    """
    def __init__(self, stream):
        self._name = cstring(stream)
        self._nparams = u8(stream)
        self._isfunc = bool(u8(stream))
        self._value = cstring(stream)

    def get_name(self):
        name = self._name.decode("ascii")
        if self._isfunc:
            name += "("
            for n in range(self._nparams):
                name += chr(0x41 + n)
                if n != self._nparams - 1:
                    name += ","
            name += ")"
        return name

    def get_value(self):
        # TODO: I don't expect this to be reliable.
        if self._isfunc:
            # Each argument is encoded as 0x80 | (n) where n is the param index.
            for i, b in enumerate(self._value):
                if b & 0x80:
                    self._value[i] = 0x41 + (b & 0x7f)
        return self._value.decode("ascii")

    def print(self):
        return f"#define {self.get_name()} {self.get_value()}\n"


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


class TILBucket:
    """Handle's unpacking a single TIL bucket."""
    def __init__(self, flags, stream):
        self._types = []
        if flags & TIL_ORD:
            self.nords = u32(stream)    # Number of ordinals

        self.ndefs = u32(stream)    # Number of definitions
        self.size = u32(stream)     # Size of uncompressed buffer
        self.buffer = None          # Buffer

        if flags & TIL_ZIP:
            csize = u32(stream)
            self.buffer = zlib.decompress(stream.read(csize))
        else:
            self.buffer = stream.read(self.size)

    def add_type(self, t):
        self._types.append(t)

    def get_types(self):
        return self._types

    def __iter__(self):
        yield from self._types


class TILHeader:
    """Parses the TIL header."""
    def __init__(self, stream):
        self._stream = stream
        self._read()

    def _read(self):
        self.sig = self._stream.read(6)
        if self.sig != b'IDATIL':
            raise ValueError("Unexpected TIL signature")

        self.form = u32(self._stream)
        if self.form > 0x12:
            raise ValueError("Unexpected TIL format")

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
        self._syms = TILBucket(self._header.flag & 0xCF, self._stream)
        self._types = TILBucket(self._header.flag, self._stream)
        self._macros = TILBucket(self._header.flag & 0xCF, self._stream)
        self._load_bucket(self._syms)
        self._load_bucket(self._types)
        self._load_macros(self._macros)
        self._process_bucket(self._syms)
        self._process_bucket(self._types)

    def _load_bucket(self, bucket):
        buffer = io.BytesIO(bucket.buffer)
        for _ in range(bucket.ndefs):
            bucket.add_type(TypeData(buffer, self._header.form))

    def _load_macros(self, bucket):
        buffer = io.BytesIO(bucket.buffer)
        for _ in range(bucket.ndefs):
            bucket.add_type(Macro(buffer))

    def _process_bucket(self, bucket):
        self._deserialize_bucket(bucket)

    def _deserialize_bucket(self, bucket):
        for tdata in bucket.get_types():
            tinfo = self.deserialize(tdata.get_type_string(),
                                     tdata.get_fields(),
                                     tdata.get_field_comments())
            if tinfo is not None:
                self._typeinfos.append(tinfo)
                tdata.set_type_info(tinfo)

    def deserialize(self, typestr, fields, fieldcmts):
        """ Deserialize a TypeString into a TypeInfo object.

        Args:
            typestr (TypeString): Input serialized type string.
            fields (TypeString): Input serialized fields p-list.
            fieldcmts (TypeString): Input serialized field comments p-list.

        Returns:
            TypeInfo: Output TypeInfo object.
        """
        typ = typestr.peek_db()
        base = typ & TYPE_BASE_MASK
        flags = typ & TYPE_FLAGS_MASK

        if base <= BT_LAST_BASIC:
            typestr += 1
            return TypeInfo(typ)

        if base > BT_LAST_BASIC:
            typedata = None
            if base == BT_COMPLEX and flags != BTMT_TYPEDEF:
                t = typestr.get()
                t += 1
                N = t.read_complex_n()
                if N == 0:
                    typedata = TypedefTypeData()
                    typedata.name = t.read_pstring().decode("ascii")
                    # I don't like this, we're going to need to come up with a
                    # way to do this automatically
                    typestr += t.pos()
                    return TypeInfo.create_type_info(typ, typedata)

            if base == BT_PTR:
                typedata = PointerTypeData() \
                    .deserialize(self, typestr, fields, fieldcmts)
            elif base == BT_ARRAY:
                typedata = ArrayTypeData() \
                    .deserialize(self, typestr, fields, fieldcmts)
            elif base == BT_FUNC:
                typedata = FuncTypeData() \
                    .deserialize(self, typestr, fields, fieldcmts)
            elif base == BT_COMPLEX:
                if flags == BTMT_STRUCT or flags == BTMT_UNION:
                    typedata = UdtTypeData() \
                        .deserialize(self, typestr, fields, fieldcmts)
                elif flags == BTMT_ENUM:
                    typedata = EnumTypeData() \
                        .deserialize(self, typestr, fields, fieldcmts)
                elif flags == BTMT_TYPEDEF:
                    typedata = TypedefTypeData() \
                        .deserialize(self, typestr, fields, fieldcmts)
            elif base == BT_BITFIELD:
                typedata = BitfieldTypeData() \
                    .deserialize(self, typestr, fields, fieldcmts)
            return TypeInfo.create_type_info(typ, typedata)

    def serialize(self, tinfo, typestr):
        """ Serialize a TypeInfo object into a TypeString.

        Args:
            tinfo (TypeInfo): Input TypeInfo object.
            typestr (TypeString): Output TypeString.
        """
        typ = tinfo.get_decl_type()
        base = typ & TYPE_BASE_MASK

        if base <= BT_LAST_BASIC:
            typestr.append_db(typ)
            return

        if base > BT_LAST_BASIC:
            details = tinfo.get_type_details()
            if details is not None:
                details.serialize(self, tinfo, typestr)

    def get_header(self):
        """ Get header information.

        Returns:
            TILHeader: The header information.
        """
        return self._header

    def get_syms(self):
        """ Get the symbol bucket.

        Returns:
            TILBucket: The symbol bucket.
        """
        return self._syms

    def get_types(self):
        """ Get the type bucket.

        Returns:
            TILBucket: The type bucket.
        """
        return self._types

    def get_macros(self):
        """ Get the macro bucket.

        Returns:
            TILBucket: The macro bucket.
        """
        return self._macros

    def get_named_type(self, name, is_type):
        """ Get named typeinfo.

        Args:
            name (str): The name of the type.
            is_type (bool): True if this is a type and otherwise for symbols.

        Returns:
            TypeData: The serialized type data.
        """
        bucket = self._types if is_type else self._syms
        for type_data in bucket.get_types():
            if name == type_data.get_name():
                return type_data
        return None

    def get_enums(self):
        enums = []
        for tdata in self._types.get_types():
            tinfo = tdata.get_type_info()
            typ = tinfo.get_decl_type()
            base = typ & TYPE_BASE_MASK
            flags = typ & TYPE_FLAGS_MASK
            if base == BT_COMPLEX and flags == BTMT_ENUM:
                enums.append(tdata)
        return enums

    def get_structs(self):
        structs = []
        for tdata in self._types.get_types():
            tinfo = tdata.get_type_info()
            typ = tinfo.get_decl_type()
            base = typ & TYPE_BASE_MASK
            flags = typ & TYPE_FLAGS_MASK
            if base == BT_COMPLEX and flags == BTMT_STRUCT:
                structs.append(tdata)
        return structs
