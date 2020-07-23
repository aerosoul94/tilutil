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
BT_INT64 = 0x06
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

_BT_LAST_BASIC = BT_FLOAT

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


class PointerTypeData:
    """Representation of ptr_type_data_t"""
    def __init__(self):
        self.obj_type = None
        self.closure = None
        self.based_ptr_size = 0
        self.taptr_bits = 0

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.readu8()
        base = typ & TYPE_BASE_MASK
        flags = typ & TYPE_FLAGS_MASK
        mod = typ & TYPE_MODIF_MASK

        if flags == BTMT_CLOSURE:
            ptr_size = typestr.readu8()
            # Next byte MUST be RESERVED_BYTE
            if ptr_size == RESERVED_BYTE:
                # and after it ::BT_FUNC
                self.closure = til.deserialize(typestr.ref())
            else:
                self.based_ptr_size = typestr.readu8()
        self.taptr_bits = typestr.read_type_attr()
        self.obj_type = til.deserialize(typestr.ref(), fields, fieldcmts)
        return self


class ArrayTypeData:
    """Representation of array_type_data_t"""
    def __init__(self):
        self.elem_type = None
        self.base = 0
        self.nelems = 0

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.readu8()
        base = typ & TYPE_BASE_MASK
        flags = typ & TYPE_FLAGS_MASK
        mod = typ & TYPE_MODIF_MASK

        if flags & BTMT_NONBASED:
            self.base = 0
            self.nelems = typestr.read_dt()
        else:
            self.nelems, self.base = typestr.read_da()
        self.elem_type = til.deserialize(typestr.get(), fields, fieldcmts)
        return self


class FuncArg:
    def __init__(self):
        self.argloc = None  # argloc_t
        self.name = ""
        self.cmt = ""
        self.type = None    # tinfo_t
        self.flags = 0


class FuncTypeData:
    def __init__(self):
        self.args = []
        self.flags = 0
        self.rettype = None     # tinfo_t
        self.retloc = None      # argloc_t
        self.stkargs = None     # uval_t
        self.spoiled = None     # reginfovec_t
        self.cc = 0

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.readu8()
        base = typ & TYPE_BASE_MASK
        flags = typ & TYPE_FLAGS_MASK
        mod = typ & TYPE_MODIF_MASK

        cm = typestr.readu8()
        if (cm & CM_CC_MASK) == CM_CC_SPOILED:
            pass
        else:
            self.flags = 0
        self.cc = cm
        self.flags |= 4 * flags
        typestr.read_type_attr()
        self.rettype = til.deserialize(typestr.ref(), fields, fieldcmts)
        cc = self.cc & CM_CC_MASK
        if cc == CM_CC_SPECIALE or cc == CM_CC_SPECIALP or cc == CM_CC_SPECIAL:
            if (self.rettype.base_type() & TYPE_FULL_MASK) == 1:
                self.retloc = self.deserialize_argloc(typestr.get())
        if cc != CM_CC_VOIDARG:
            N = typestr.read_dt()
            if N > 256:
                raise ValueError("invalid arg count!")
            if N > 0:
                for n in range(N):
                    arg = FuncArg()
                    if fields is not None and n < len(fields):
                        arg.name = fields[n]
                    fah = typestr.peeku8()
                    if fah == FAH_BYTE:
                        typestr.seek(1)
                        arg.flags = typestr.read_de()
                    arg.type = til.deserialize(typestr.ref(),
                                               fields, fieldcmts)
                    if self.cc == CM_CC_SPECIALE or \
                        self.cc == CM_CC_SPECIALP or \
                            self.cc == CM_CC_SPECIAL:
                        arg.argloc = self.deserialize_argloc(typestr.get())
                    self.args.append(arg)
        return self

    def deserialize_argloc(self, typestr):
        raise NotImplementedError("extract_argloc() not implemented.")


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


class UdtTypeData:
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
        typ = typestr.readu8()
        base = typ & TYPE_BASE_MASK
        flags = typ & TYPE_FLAGS_MASK
        mod = typ & TYPE_MODIF_MASK

        N = typestr.read_complex_n()
        if N == 0:
            # TODO: I don't think this code is necessary anymore
            string = typestr.read_pstring()
            if len(string) > 1 and string[0] == "#":
                raise NotImplementedError("type ordinals not implemented.")
            # TODO: Need to implement struct references
        else:
            attr = typestr.read_sdacl_attr()
            ALPOW = N & 7
            MCNT = N >> 3
            self.pack = ALPOW
            if attr is not None:
                self.taudt_bits = attr
            for n in range(MCNT):
                member = UdtMember()
                if fields is not None and n < len(fields):
                    member.name = fields[n]
                if fieldcmts is not None and n < len(fieldcmts):
                    member.cmt = fieldcmts[n]
                member.type = til.deserialize(typestr.ref(),
                                              fields,
                                              fieldcmts)
                attr = typestr.read_sdacl_attr()
                if attr is not None:
                    member.tafld_bits = attr
                    member.fda = attr & 0xf
                self.members.append(member)
        return self


class EnumMember:
    def __init__(self):
        self.name = None    # qstring
        self.cmt = None     # qstring
        self.value = 0


class EnumTypeData:
    """Representation of enum_type_data_t"""
    def __init__(self):
        self.group_sizes = []   # intvec_t (qvector<int>)
        self.taenum_bits = 0
        self.bte = 0
        self.members = []

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.readu8()
        base = typ & TYPE_BASE_MASK
        flags = typ & TYPE_FLAGS_MASK
        mod = typ & TYPE_MODIF_MASK

        N = typestr.read_complex_n()
        taenum_bits = typestr.read_type_attr()
        self.taenum_bits = taenum_bits if taenum_bits is not None else 0
        self.bte = typestr.readu8()
        if not (self.bte & BTE_ALWAYS):
            return
        mask = self.calc_mask(til)
        offset = 0
        lo = 0
        hi = 0
        for m in range(N):
            member = EnumMember()
            if fields is not None:
                if m < len(fields):
                    member.name = fields[m]
                # else:
                #     raise IndexError("m does not index fields")
            if fieldcmts is not None:
                if m < len(fieldcmts):
                    member.cmt = fieldcmts[m]
                # else
                #    raise IndexError("m does not index fieldcmts")
            lo = typestr.read_de()
            if self.taenum_bits & TAENUM_64BIT:
                hi = typestr.read_de()
            if self.bte & BTE_BITFIELD:
                self.group_sizes.append(typestr.read_dt())
            member.value = (lo | (hi << 32)) & mask
            self.members.append(member)
        return self

    def calc_mask(self, til):
        emsize = self.bte & BTE_SIZE_MASK
        if emsize != 0:
            bytesize = 1 << (emsize - 1)
        else:
            bytesize = til.header().size_e
        # elif (ph.flag >> 12) & 1:
        #    mask = ph.nortify(ev_get_default_enum_size)
        # else:
        #    mask = -1
        bitsize = bytesize * 8
        if bitsize < 64:
            return (1 << bitsize) - 1
        return 0xffffffffffffffff


class TypedefTypeData:
    """Representation of typedef_type_data_t"""
    def __init__(self):
        self.til = None
        self.name = None
        self.ordinal = 0
        self.is_ordref = False
        self.resolve = False

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.readu8()
        base = typ & TYPE_BASE_MASK
        flags = typ & TYPE_FLAGS_MASK
        mod = typ & TYPE_MODIF_MASK

        self.til = til
        string = typestr.read_pstring()
        if len(string) > 1 and string[0] == "#":
            self.is_ordref = True
            self.name = string
        else:
            self.name = string
        return self


class BitfieldTypeData:
    """Representation of bitfield_type_data_t"""
    def __init__(self):
        self.nbytes = 0
        self.width = 0
        self.is_unsigned = False

    def deserialize(self, til, typestr, fields, fieldcmts):
        typ = typestr.readu8()
        base = typ & TYPE_BASE_MASK
        flags = typ & TYPE_FLAGS_MASK
        mod = typ & TYPE_MODIF_MASK

        dt = typestr.read_dt()
        self.nbytes = 1 << (flags >> 4)
        self.width = dt >> 1
        self.is_unsigned = dt & 1
        return self

