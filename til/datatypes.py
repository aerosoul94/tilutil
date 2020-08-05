from abc import ABCMeta, abstractmethod
from .tilfile import *
from .utils import *

RESERVED_BYTE = 0xFF

TYPE_BASE_MASK = 0x0F
TYPE_FLAGS_MASK = 0x30
TYPE_MODIF_MASK = 0xC0

TYPE_FULL_MASK = TYPE_BASE_MASK | TYPE_FLAGS_MASK

BT_UNK = 0x00
BT_VOID = 0x01
BTMT_SIZE0 = 0x00
BTMT_SIZE12 = 0x10
BTMT_SIZE48 = 0x20
BTMT_SIZE128 = 0x30

BT_INT8 = 0x02
BT_INT16 = 0x03
BT_INT32 = 0x04
BT_INT64 = 0x05
BT_INT128 = 0x06
BT_INT = 0x07
BTMT_UNKSIGN = 0x00
BTMT_SIGNED = 0x10
BTMT_USIGNED = 0x20
BTMT_UNSIGNED = BTMT_USIGNED
BTMT_CHAR = 0x30

BT_BOOL = 0x08
BTMT_DEFBOOL = 0x00
BTMT_BOOL1 = 0x10
BTMT_BOOL2 = 0x20
BTMT_BOOL4 = 0x30

BT_FLOAT = 0x09
BTMT_FLOAT = 0x00
BTMT_DOUBLE = 0x10
BTMT_LNGDBL = 0x20
BTMT_SPECFLT = 0x30

BT_LAST_BASIC = BT_FLOAT

BT_PTR = 0x0A
BTMT_DEFPTR = 0x00
BTMT_NEAR = 0x10
BTMT_FAR = 0x20
BTMT_CLOSURE = 0x30

BT_ARRAY = 0x0B
BTMT_NONBASED = 0x10
BTMT_ARRESERV = 0x20

BT_FUNC = 0x0C
BTMT_DEFCALL = 0x00
BTMT_NEARCALL = 0x10
BTMT_FARCALL = 0x20
BTMT_INTCALL = 0x30

BT_COMPLEX = 0x0D
BTMT_STRUCT = 0x00
BTMT_UNION = 0x10
BTMT_ENUM = 0x20
BTMT_TYPEDEF = 0x30

BT_BITFIELD = 0x0E
BTMT_BFLDI8 = 0x00
BTMT_BFLDI16 = 0x10
BTMT_BFLDI32 = 0x20
BTMT_BFLDI64 = 0x30

BT_RESERVED = 0x0F

BTM_CONST = 0x40
BTM_VOLATILE = 0x80

BTE_SIZE_MASK = 0x07
BTE_RESERVED = 0x08
BTE_BITFIELD = 0x10
BTE_OUT_MASK = 0x60
BTE_HEX = 0x00
BTE_CHAR = 0x20
BTE_SDEC = 0x40
BTE_UDEC = 0x60
BTE_ALWAYS = 0x80

BTF_STRUCT = BT_COMPLEX | BTMT_STRUCT
BTF_UNION = BT_COMPLEX | BTMT_UNION
BTF_ENUM = BT_COMPLEX | BTMT_ENUM
BTF_TYPEDEF = BT_COMPLEX | BTMT_TYPEDEF

TAH_BYTE = 0xFE
FAH_BYTE = 0xFF

TAH_HASATTRS = 0x0010

TAUDT_UNALIGNED = 0x0040
TAUDT_MSSTRUCT = 0x0020
TAUDT_CPPOBJ = 0x0080

TAFLD_BASECLASS = 0x0020
TAFLD_UNALIGNED = 0x0040
TAFLD_VIRTBASE = 0x0080

TAPTR_PTR32 = 0x0020
TAPTR_PTR64 = 0x0040
TAPTR_RESTRICT = 0x0060

TAENUM_64BIT = 0x0020

CM_MASK = 0x03
CM_UNKNOWN = 0x00
CM_N8_F16 = 0x01
CM_N64 = 0x01
CM_N16_F32 = 0x02
CM_N32_F48 = 0x03

CM_M_MASK = 0x0C
CM_M_MN = 0x00
CM_M_FF = 0x04
CM_M_NF = 0x08
CM_M_FN = 0x0C

CM_CC_MASK = 0xF0
CM_CC_INVALID = 0x00
CM_CC_UNKNOWN = 0x10
CM_CC_VOIDARG = 0x20

CM_CC_CDECL = 0x30
CM_CC_ELLIPSIS = 0x40
CM_CC_STDCALL = 0x50
CM_CC_PASCAL = 0x60
CM_CC_FASTCALL = 0x70
CM_CC_THISCALL = 0x80
CM_CC_MANUAL = 0x90
CM_CC_SPOILED = 0xA0

CM_CC_RESERVE4 = 0xB0
CM_CC_RESERVE3 = 0xC0
CM_CC_SPECIALE = 0xD0
CM_CC_SPECIALP = 0xE0
CM_CC_SPECIAL = 0xF0


def print_type(tinfo, name):
    typ = tinfo.get_decl_type()
    base = typ & TYPE_BASE_MASK
    flags = typ & TYPE_FLAGS_MASK
    mod = typ & TYPE_MODIF_MASK
    res = ""
    if mod & BTM_CONST:
        res += "const "
    if mod & BTM_VOLATILE:
        res += "volatile "
    if base <= BT_LAST_BASIC:
        if base == BT_UNK:
            if flags == BTMT_SIZE12:
                return "_WORD"
            elif flags == BTMT_SIZE48:
                return "_QWORD"
            elif flags == BTMT_SIZE128:
                return "_UNKNOWN"
        if base == BT_VOID:
            if flags == BTMT_SIZE12:
                return "_BYTE"
            elif flags == BTMT_SIZE48:
                return "_DWORD"
            elif flags == BTMT_SIZE128:
                return "_OWORD"
            else:
                return "void"
        elif base <= BT_INT:
            if flags & BTMT_SIGNED:
                res += "signed "
            elif flags & BTMT_UNSIGNED:
                res += "unsigned "
            elif flags & BTMT_CHAR:
                return res + "char"
            if base == BT_INT8:
                return res + "__int8"
            elif base == BT_INT16:
                return res + "__int16"
            elif base == BT_INT32:
                return res + "__int32"
            elif base == BT_INT64:
                return res + "__int64"
            elif base == BT_INT128:
                return res + "__int128"
            elif base == BT_INT:
                return res + "int"
        elif base == BT_BOOL:
            if flags == BTMT_BOOL1:
                return "_BOOL1"
            elif flags == BTMT_BOOL2:
                #return "_BOOL8" if inf.is_64bit() else "_BOOL2"
                return "_BOOL2"
            elif flags == BTMT_BOOL4:
                return "_BOOL4"
            else:
                return "bool"
        elif base == BT_FLOAT:
            if flags == BTMT_FLOAT:
                return "float"
            elif flags == BTMT_DOUBLE:
                return "double"
            elif flags == BTMT_LNGDBL:
                return "long double"
            elif flags == BTMT_SPECFLT:
                return "short float"
            #     return "_TBYTE" if ph.flags & PR_USE_TBYTE else "short float"
    elif base > BT_LAST_BASIC:
        details = tinfo.get_type_details()
        return details.print_type(name)


class BaseTypeData:
    __metaclass__ = ABCMeta

    @abstractmethod
    def deserialize(self, til, typestr, fields, fieldcmts):
        """Deserialize a type string into a TypeInfo object.

        Args:
            til (TIL): Type info library
            typestr (TypeString): Type string
            fields (TypeString): List of field names
            fieldcmts (TypeString): List of field comments

        Returns:
            BaseTypeData: Deserialized type data
        """
        raise NotImplementedError()

    @abstractmethod
    def serialize(self, til, tinfo, typestr, fields, fieldcmts):
        """Serialize a TypeInfo object into a type string.

        Args:
            til (TIL): Type info library
            tinfo (TypeInfo): Input TypeInfo object
            typestr (TypeString): Type string
            fields (TypeString): List of field names
            fieldcmts (TypeString): List of field comments
        """
        raise NotImplementedError()

    @abstractmethod
    def print_type(self, name):
        """Print this type using name as the type name.

        Args:
            name (str): Type name

        Returns:
            str: Printed type
        """
        raise NotImplementedError()


class PointerTypeData(BaseTypeData):
    """Representation of ptr_type_data_t"""
    def __init__(self):
        self.obj_type = None
        self.closure = None
        self.based_ptr_size = 0
        self.taptr_bits = 0

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.read_db()
        flags = typ & TYPE_FLAGS_MASK

        if flags == BTMT_CLOSURE:
            ptr_size = typestr.read_db()
            # Next byte MUST be RESERVED_BYTE
            if ptr_size == RESERVED_BYTE:
                # and after it ::BT_FUNC
                self.closure = til.deserialize(typestr, fields, fieldcmts)
            else:
                self.based_ptr_size = typestr.read_db()
        self.taptr_bits = typestr.read_type_attr()
        self.obj_type = til.deserialize(typestr, fields, fieldcmts)
        return self

    def serialize(self, til, tinfo, typestr, fields, fieldcmts):
        typ = tinfo.get_decl_type()

        # append type byte
        typestr.append_db(typ)
        til.serialize(self.obj_type, typestr)

    def print_type(self, name):
        obj_type = self.obj_type
        if obj_type.is_func():
            details = obj_type.get_type_details()
            ret_type = print_type(details.rettype, "")
            args = ""
            for n, arg in enumerate(details.args):
                args += print_type(arg.type, "")
                if arg.name:
                    args += " " + arg.name
                if n != len(details.args) - 1:
                    args += ", "
            return "{} (* {})({})".format(ret_type, name, args)
        base_type = print_type(obj_type, "")
        if name:
            return "{}* {}".format(base_type, name)
        return "{}*".format(base_type)


class ArrayTypeData(BaseTypeData):
    """Representation of array_type_data_t"""
    def __init__(self):
        self.elem_type = None
        self.base = 0
        self.nelems = 0

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.read_db()
        flags = typ & TYPE_FLAGS_MASK

        if flags & BTMT_NONBASED:
            self.base = 0
            self.nelems = typestr.read_dt()
        else:
            _, self.nelems, self.base = typestr.read_da()
        self.elem_type = til.deserialize(typestr, fields, fieldcmts)
        return self

    def serialize(self, til, tinfo, typestr, fields, fieldcmts):
        typ = tinfo.get_decl_type()
        flags = typ & TYPE_FLAGS_MASK

        typestr.append_db(typ)
        if flags & BTMT_NONBASED:
            typestr.append_dt(self.nelems)
        else:
            typestr.append_da(self.nelems, self.base)
        til.serialize(self.elem_type, typestr)

    def print_type(self, name):
        elem_type = self.elem_type
        array = "[{}]".format(self.nelems)
        while elem_type.is_array():
            details = elem_type.get_type_details()
            array += "[{}]".format(details.nelems)
            elem_type = details.elem_type
        base_type = print_type(elem_type, "")
        return "{} {}{}".format(base_type, name, array)


ALOC_NONE = 0
ALOC_STACK = 1
ALOC_DIST = 2
ALOC_REG1 = 3
ALOC_REG2 = 4
ALOC_RREL = 5
ALOC_STATIC = 6
ALOC_CUSTOM = 7


class ArgLoc:
    def __init__(self):
        self.type = 0


class RegInfo:
    def __init__(self):
        self.reg = 0
        self.size = 0


class FuncArg:
    def __init__(self):
        self.argloc = None  # argloc_t
        self.name = ""
        self.cmt = ""
        self.type = None    # tinfo_t
        self.flags = 0


class FuncTypeData(BaseTypeData):
    def __init__(self):
        self.args = []
        self.flags = 0          # FTI_*
        self.rettype = None     # tinfo_t
        self.retloc = None      # argloc_t
        self.stkargs = None     # uval_t
        self.spoiled = None     # reginfovec_t
        self.cc = 0

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.read_db()
        flags = typ & TYPE_FLAGS_MASK

        self.extract_spoiled(typestr)
        self.cc = typestr.read_db()
        self.flags |= 4 * flags
        typestr.read_type_attr()
        self.rettype = til.deserialize(typestr, fields, fieldcmts)
        cc = self.cc & CM_CC_MASK
        if cc > CM_CC_SPECIALE:
            if (self.rettype.get_decl_type() & TYPE_FULL_MASK) != BT_VOID:
                self.retloc = self.extract_argloc(typestr)
        if cc != CM_CC_VOIDARG:
            N = typestr.read_dt()
            if N > 256:
                raise ValueError("Invalid arg count!")
            if N > 0:
                for n in range(N):
                    arg = FuncArg()
                    if fields is not None:
                        arg.name = fields.read_pstring().decode("ascii")
                    if fieldcmts is not None:
                        arg.cmt = fieldcmts.read_pstring().decode("ascii")
                    fah = typestr.peek_db()
                    if fah == FAH_BYTE:
                        typestr.seek(1)
                        arg.flags = typestr.read_de()
                    arg.type = til.deserialize(typestr, fields, fieldcmts)
                    if cc > CM_CC_SPECIALE:
                        arg.argloc = self.extract_argloc(typestr)
                    self.args.append(arg)
        return self

    def extract_spoiled(self, typestr):
        # TODO: NOT FULLY TESTED
        cm = typestr.peek_db()
        if (cm & CM_CC_MASK) == CM_CC_SPOILED:
            while True:
                typestr.seek(1)
                if (cm & ~CM_CC_MASK) == 15:
                    f = 2 * (typestr.read_db() & 0x1f)
                else:
                    nspoiled = cm & ~CM_CC_MASK
                    for n in range(nspoiled):
                        reginfo = RegInfo()
                        b = typestr.read_db()
                        if bool(b & 0x80):
                            size = typestr.read_db()
                            reg = b & 0x7f
                        else:
                            size = (b >> 4) + 1
                            reg = (b & 0xf) - 1
                        reginfo.size = size
                        reginfo.reg = reg
                        self.spoiled.append(reginfo)
                    f = 1
                cm = typestr.peek_db()
                self.flags |= f
                if (cm & CM_CC_MASK) != CM_CC_SPOILED:
                    break
        else:
            self.flags = 0

    def extract_argloc(self, typestr):
        # TODO: NOT FULLY TESTED
        argloc = ArgLoc()
        a = typestr.read_db()
        if a == 0xff:
            argloc.type = typestr.read_dt()
            if argloc.type == ALOC_STACK:
                # fills sval
                typestr.read_de()   # sval
            elif argloc.type == ALOC_DIST:
                pass
            elif argloc.type in (ALOC_REG1, ALOC_REG2):
                # fills reginfo (offset and register ndx)
                typestr.read_dt()   # reginfo
                typestr.read_dt()   # reginfo << 16
            elif argloc.type == ALOC_RREL:
                # fills rrel
                typestr.read_dt()   # rrel_t->reg
                typestr.read_de()   # rrel_t->off
            elif argloc.type == ALOC_STATIC:
                # fills sval
                typestr.read_de()
        else:
            b = (a & 0x7f) - 1
            if b <= 0x80:
                if b & 0x7f:
                    # argloc.type = ALLOC_REG1
                    # argloc.sval = b
                    pass
                else:
                    # argloc.type = ALLOC_STACK
                    # argloc.sval = 0
                    pass
            else:
                c = typestr.read_db() - 1
                if c != -1:
                    # argloc.type = ALLOC_REG2
                    # argloc.reginfo = b | (c << 16)
                    pass
        return argloc

    def serialize(self, til, tinfo, typestr, fields, fieldcmts):
        typ = tinfo.get_decl_type()

        typestr.append_db(typ)
        typestr.append_db(self.cc)
        til.serialize(self.rettype, typestr)
        N = len(self.args)
        typestr.append_dt(N)
        for arg in self.args:
            til.serialize(arg.type, typestr)

    def print_type(self, name):
        res = print_type(self.rettype, "") + " "
        cc = self.cc & CM_CC_MASK
        if cc == CM_CC_INVALID:
            res += "__bad_cc "
        elif cc == CM_CC_CDECL:
            res += "__cdecl "
        elif cc == CM_CC_STDCALL:
            res += "__stdcall "
        elif cc == CM_CC_PASCAL:
            res += "__pascal "
        elif cc == CM_CC_FASTCALL:
            res += "__fastcall "
        elif cc == CM_CC_THISCALL:
            res += "__thiscall "
        elif cc in (CM_CC_SPECIALE, CM_CC_SPECIAL):
            res += "__usercall "
        elif cc == CM_CC_SPECIALP:
            res += "__userpurge "
        res += name
        args = ""
        for n, arg in enumerate(self.args):
            args += print_type(arg.type, "")
            if arg.name:
                args += " " + arg.name
            if n != len(self.args) - 1:
                args += ", "
        res += "(" + args + ")"
        return res


class UdtMember:
    def __init__(self):
        self.offset = 0
        self.size = 0
        self.name = None    # qstring
        self.cmt = None     # qstring
        self.type = None    # tinfo_t
        self.effalign = 0
        self.tafld_bits = 0
        self.fda = 0


class UdtTypeData(BaseTypeData):
    """Representation of udt_type_data_t"""
    def __init__(self):
        self.members = []
        self.total_size = 0
        self.unpadded_size = 0
        self.effalign = 0
        self.taudt_bits = 0
        self.sda = 0
        self.pack = 0
        self.is_union = False

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.read_db()

        self.is_union = (typ & TYPE_FULL_MASK) == BTF_UNION
        N = typestr.read_complex_n()
        if N == 0:
            raise ValueError("Should have been parsed as typedef")
        alpow = N & 7
        mcnt = N >> 3
        self.pack = alpow
        attr = typestr.read_sdacl_attr()
        if attr is not None:
            self.taudt_bits = attr
        for n in range(mcnt):
            member = UdtMember()
            if fields is not None:
                member.name = fields.read_pstring().decode("ascii")
            if fieldcmts is not None:
                member.cmt = fieldcmts.read_pstring()
            member.type = til.deserialize(typestr, fields, fieldcmts)
            attr = typestr.read_sdacl_attr()
            if attr is not None:
                member.tafld_bits = attr
                member.fda = attr & 0xf
            self.members.append(member)
        return self

    def serialize(self, til, tinfo, typestr, fields, fieldcmts):
        typ = tinfo.get_decl_type()

        typestr.append_db(typ)
        mcnt = len(self.members)
        alpow = self.pack
        N = mcnt << 3 | alpow & 7
        typestr.append_complex_n(N, False)
        for member in self.members:
            til.serialize(member.type, typestr)
            if fields is not None and member.name:
                fields.append_pstring(member.name)
            if fieldcmts is not None and member.cmt:
                fieldcmts.append_pstring(member.cmt)

    def print_type(self, name):
        res = "union " if self.is_union else "struct "
        if self.taudt_bits & TAUDT_MSSTRUCT:
            res += "__attribute__((msstruct)) "
        if self.taudt_bits & TAUDT_CPPOBJ:
            res += "__cppobj "
        res += name + " "
        for i, member in enumerate(self.members):
            if member.tafld_bits & TAFLD_BASECLASS:
                res += ": " if i == 0 else ", "
                res += print_type(member.type, "")
        res += "\n"
        res += "{\n"
        for member in self.members:
            if member.tafld_bits & TAFLD_BASECLASS:
                continue
            membertype = member.type
            res += "  "
            if membertype.is_ptr() or membertype.is_array():
                field = print_type(member.type, member.name)
                res += "{};\n".format(field)
            elif membertype.is_bitfield():
                details = membertype.get_type_details()
                flags = membertype.get_type_flags()
                if flags == BTMT_BFLDI8:
                    res += "__int8"
                elif flags == BTMT_BFLDI16:
                    res += "__int16"
                elif flags == BTMT_BFLDI32:
                    res += "__int32"
                elif flags == BTMT_BFLDI64:
                    res += "__int64"
                res += " {} : {};\n".format(member.name, details.width)
            else:
                field = print_type(member.type, "")
                res += "{} {};\n".format(field, member.name)
        res += "}"
        return res


class EnumMember:
    def __init__(self):
        self.name = None    # qstring
        self.cmt = None     # qstring
        self.value = 0


class EnumTypeData(BaseTypeData):
    """Representation of enum_type_data_t"""
    def __init__(self):
        self.group_sizes = []   # intvec_t (qvector<int>)
        self.taenum_bits = 0
        self.bte = 0
        self.members = []

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.read_db()

        N = typestr.read_complex_n()
        if N == 0:
            raise ValueError("Should have been parsed as typedef")
        attr = typestr.read_type_attr()
        if attr is not None:
            self.taenum_bits = attr
        self.bte = typestr.read_db()
        if not (self.bte & BTE_ALWAYS):
            raise ValueError("Enum bte must have BTE_ALWAYS set")
        mask = self.calc_mask(til)
        delta = 0
        hi = 0
        for m in range(N):
            member = EnumMember()
            if fields is not None:
                member.name = fields.read_pstring().decode("ascii")
            if fieldcmts is not None:
                member.cmt = fieldcmts.read_pstring().decode("ascii")
            lo = typestr.read_de()
            if self.taenum_bits & TAENUM_64BIT:
                hi = typestr.read_de()
            if self.bte & BTE_BITFIELD:
                self.group_sizes.append(typestr.read_dt())
            delta += to_s32((lo | (hi << 32)) & mask)
            member.value = delta
            self.members.append(member)
        return self

    def calc_mask(self, til):
        emsize = self.bte & BTE_SIZE_MASK
        if emsize != 0:
            bytesize = 1 << (emsize - 1)
        else:
            bytesize = til.get_header().size_e
        # elif (ph.flag >> 12) & 1:
        #    mask = ph.notify(ev_get_default_enum_size)
        # else:
        #    mask = -1
        bitsize = bytesize * 8
        if bitsize < 64:
            return (1 << bitsize) - 1
        return 0xffffffffffffffff

    def serialize(self, til, tinfo, typestr, fields, fieldcmts):
        typ = tinfo.get_decl_type()

        typestr.append_db(typ)
        N = len(self.members)
        typestr.append_complex_n(N, False)
        typestr.append_db(self.bte)
        prev = 0
        for member in self.members:
            curr = member.value
            delta = curr - prev
            prev = curr
            typestr.append_de(delta)

    def print_type(self, name):
        res = "enum {}\n".format(name)
        res += "{\n"
        out = self.bte & BTE_OUT_MASK
        for member in self.members:
            value = member.value
            if out == BTE_HEX:
                value = hex(member.value)
            res += "  {} = {},\n".format(member.name, value)
        res += "}"
        return res


class TypedefTypeData(BaseTypeData):
    """Representation of typedef_type_data_t"""
    def __init__(self):
        self.til = None
        self.name = None
        self.ordinal = 0
        self.is_ordref = False
        self.resolve = False

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.read_db()

        self.til = til
        string = typestr.read_pstring()
        if len(string) > 1 and string[0] == b"#":
            self.is_ordref = True
            self.name = string
        else:
            self.name = string.decode("ascii")
        return self

    def serialize(self, til, tinfo, typestr, fields, fieldcmts):
        typ = tinfo.get_decl_type()

        typestr.append_db(typ)
        typestr.append_pstring(self.name)

    def print_type(self, name):
        if name:
            return "typedef {} {}".format(self.name, name)
        else:
            return "{}".format(self.name)


class BitfieldTypeData(BaseTypeData):
    """Representation of bitfield_type_data_t"""
    def __init__(self):
        self.nbytes = 0
        self.width = 0
        self.is_unsigned = False

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.read_db()
        flags = typ & TYPE_FLAGS_MASK

        dt = typestr.read_dt()
        self.nbytes = 1 << (flags >> 4)
        self.width = dt >> 1
        self.is_unsigned = dt & 1
        typestr.read_type_attr()
        return self

    def serialize(self, til, tinfo, typestr, fields, fieldcmts):
        typ = tinfo.get_decl_type()

        typestr.append_db(typ)
        typestr.append_dt(self.width << 1 | self.is_unsigned)

    def print_type(self, name):
        return "{} : {}".format(name, self.width)

