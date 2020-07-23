#NOTE: OLD CODE. THIS IS HERE JUST FOR REFERENCE

import struct
import sys
import zlib
import io
    
def u8(inp):
    return struct.unpack('<B', inp.read(1))[0]

def u16(inp):
    return struct.unpack('<H', inp.read(2))[0]

def u32(inp):
    return struct.unpack('<I', inp.read(4))[0]

def u64(inp):
    return struct.unpack('<Q', inp.read(8))[0]

def c_string(inp):
    str = []
    while True:
        c = inp.read(1)
        if c == chr(0):
            return "".join(str)
        str.append(c)

def t_string(inp): # with null byte
    str = []
    while True:
        c = inp.read(1)
        str.append(c)
        if c == chr(0):
            return "".join(str)

type_bases = {
    0x0:"BT_UNK",
    0x1:"BT_VOID",
    0x2:"BT_INT8",
    0x3:"BT_INT16",
    0x4:"BT_INT32",
    0x5:"BT_INT64",
    0x6:"BT_INT128",
    0x7:"BT_INT",
    0x8:"BT_BOOL",
    0x9:"BT_FLOAT",
    0xA:"BT_PTR",
    0xB:"BT_ARRAY",
    0xC:"BT_FUNC",
    0xD:"BT_COMPLEX",
    0xE:"BT_BITFIELD",
    0xF:"BT_RESERVED"
}

type_modifiers = {
    0x40:"BT_CONST",
    0x80:"BT_VOLATILE"
}

void_flags = {
    0x00:"BTMT_SIZE0",
    0x10:"BTMT_SIZE12",
    0x20:"BTMT_SIZE48",
    0x30:"BTMT_SIZE128"
}

int_flags = {
    0x00:"BTMT_UNKSIGN",
    0x10:"BTMT_SIGNED",
    0x20:"BTMT_USIGNED",
    0x30:"BTMT_CHAR"
}

bool_flags = {
    0x00:"BTMT_DEFBOOL",
    0x10:"BTMT_BOOL1",
    0x20:"BTMT_BOOL2",
    0x20:"BTMT_BOOL8",
    0x30:"BTMT_BOOL4",
}

float_flags = {
    0x00:"BTMT_FLOAT",
    0x10:"BTMT_DOUBLE",
    0x20:"BTMT_LNGDBL",
    0x30:"BTMT_SPECFLT"
}

ptr_flags = {
    0x00:"BTMT_DEFPTR",
    0x10:"BTMT_NEAR",
    0x20:"BTMT_FAR",
    0x30:"BTMT_CLOSURE"
}

array_flags = {
    0x10:"BTMT_NONBASED",
    0x20:"BTMT_ARRESERV"
}

func_flags = {
    0x00:"BTMT_DEFCALL",
    0x10:"BTMT_NEARCALL",
    0x20:"BTMT_FARCALL",
    0x30:"BTMT_INTCALL"
}

complex_flags = {
    0x00:"BTMT_STRUCT",
    0x10:"BTMT_UNION",
    0x20:"BTMT_ENUM",
    0x30:"BTMT_TYPEDEF"
}

bitfield_flags = {
    0x00:"BTMT_BFLDI8",
    0x10:"BTMT_BFLDI16",
    0x20:"BTMT_BFLDI32",
    0x30:"BTMT_BFLDI64"
}

type_flags = {
    0x0:void_flags,
    0x1:void_flags,
    0x2:int_flags,
    0x3:int_flags,
    0x4:int_flags,
    0x5:int_flags,
    0x6:int_flags,
    0x7:int_flags,
    0x8:bool_flags,
    0x9:float_flags,
    0xA:ptr_flags,
    0xB:array_flags,
    0xC:func_flags,
    0xD:complex_flags,
    0xE:bitfield_flags,
    0xF:None
}

TYPE_BASE_MASK = 0x0F
TYPE_FLAGS_MASK = 0x30
TYPE_MODIF_MASK = 0xC0

def get_dt(ti):
    dt = ord(ti[0])
    l = 1
    if dt & 0x80: # if sign flag is set
        l = 2
        dt = (dt & 0x7f | ord(ti[1]) << 7)
    return (dt - 1, l)

sym_name = None
sym_indx = 0

def toSigned32(n):
    n = n & 0xffffffff
    return n | (-(n & 0x80000000))

def get_de(ti):
    p = 0
    h = 0
    lo = 0
    hi = 0
    while True:
        t = ord(ti[p])
        p+=1
        hi = h << 6
        if not (t & 0x80):
            lo = t & 0x3f
        else:
            lo = 2 * hi
            hi = t & 0x7f
        h = lo | hi
        if not (t & 0x80):
            break
    return (toSigned32(h), p)

def get_da(ti):
    raise NotImplementedError

    return (0, 0, 0)

def get_complex_n(ti):
    n, len = get_dt(ti)
    if n == 0x7FFE:
        n, len = get_de(ti[2:])
        len += 2
    return (n, len)

def print_bte(bte):
    if bte & 0x10:
        print "bitfield"
    if bte & 0x7:
        print "storage size: {0}".format((1 << ((bte & 7) - 1)))
    else:
        print "storage size: default"
    style = bte & 0x60
    if style == 0:
        print "output: hex"
    elif style == 0x20:
        print "output: char"
    elif style == 0x40:
        print "output: signed dec"
    elif style == 0x60:
        print "output: unsigned dec"

def print_p_string(p_str):
    dt, length = get_dt(p_str)
    print '{0}'.format(p_str[length:length+dt])
    return length + dt

def print_p_list(p_list):
    pos = 0
    while pos < len(p_list):
        pos += print_p_string(p_list[pos:])

# TODO: determine what to do with this info
def print_type_attr(ti):
    pos = 0
    tah_byte = ord(ti[pos])
    res = 0
    tmp = ((tah_byte & 1) | ((tah_byte >> 3) & 6)) + 1
    pos += 1
    if tah_byte == 0xFE or tmp == 8:
        if tmp == 8:
            res = tmp
        next_byte = ord(ti[pos])
        shift = 0
        while True:
            pos += 1
            res |= (next_byte & 0x7f) << shift
            if next_byte & 0x80 == 0:
                break
            shift += 7
            next_byte = ord(ti[pos])
            if next_byte == 0:
                raise Exception("somethings wrong?")
    if res & 0x10:  # TAH_HASATTRS
        dt, tilen = get_dt(ti[pos:])
        pos += tilen
        for x in xrange(dt):
            pos += print_p_string(ti[pos:])
            dta, tilen = get_dt(ti[pos:])
            pos += tilen
            pos += dta # dta len of bytes
    return pos
    raise NotImplementedError

def print_argloc(ti):
    raise NotImplementedError

def print_spoiled_reg(ti):
    raise NotImplementedError

def is_sdacl_byte(t):
    t = ord(t)
    return ((t & 0xCF) ^ 0xC0) <= 1

""" Prints type info string
    Args:
        ti: type info string
        name: name of type

    Returns:
        Length of this type info string.
"""
def print_type_info(ti,name=None):
    pos = 0
    typ = ord(ti[pos])

    base = typ & TYPE_BASE_MASK
    flags = typ & TYPE_FLAGS_MASK
    mod = typ & TYPE_MODIF_MASK

    print "<type>"

    if name != None:
        print name

    mod_flags = type_modifiers.get(mod)
    if mod_flags != None:
        print mod_flags

    print type_bases.get(base)

    base_flags = type_flags.get(base)
    if base_flags != None:
        print base_flags.get(flags)

    pos += 1 # skip past type_t
    
    if base < 9:
        tah_byte = ord(ti[pos])
        if tah_byte == 0xFE:
            pos += print_type_attr(ti[pos:])

    if base == 0xA: # BT_PTR
        if flags == 0x30: # BTMT_CLOSURE
            ptr_size = ord(ti[pos])
            pos += 1
            if ptr_size == 0xFF: # RESERVED_BYTE
                pos += print_type_info(ti[pos:])
        tah_byte = ord(ti[pos])
        if tah_byte == 0xFE:
            pos += print_type_attr(ti[pos:])
        pos += print_type_info(ti[pos:])
        #pos += 1
    elif base == 0xB:   # BT_ARRAY
        #pos += 1
        if flags & 0x10:
            num_elem, size = get_dt(ti[pos:]) # nelems
            # tah-typeattrs
            print 'num_elem: {0}'.format(num_elem)
            pos += size
        else:
            num_elem, base, size = get_da(ti[pos]) # nelems
            # tah-typeattrs
            print "num_elem: {0} base: {1}".format(num_elem, base)
            pos += size
        tah_byte = ord(ti[pos])
        if tah_byte == 0xFE:    # TAH_BYTE
            pos += print_type_attr(ti[pos:])
        pos += print_type_info(ti[pos:])    # elem_type
    elif base == 0xC:   # BT_FUNC
        # either here or after SPOILED info
        cm = ord(ti[pos])
        pos += 1 # skip past cm_t byte
        # optional
        if (cm & 0xF0) == 0xA0:    # (cm & CM_CC_MASK) == CM_CC_SPOILED
            num_of_spoiled_reg = cm & 0x0F # low nibble is count
            if num_of_spoiled_reg == 15:
                bfa = ord(ti[pos])  # function attribute byte (see BFA_*)
                pos += 1
            else: # spoiled_reg_info[num_of_spoiled_regs] see extract_spoiledreg
                pos += print_spoiled_reg(ti[pos:])
            cm = ord(ti[pos]) # present real cm
            pos += 1
        # return type
        cc = cm & 0xF0 # calling convention
        # TODO: <- tah-typeattrs
        tah_byte = ord(ti[pos])
        if tah_byte == 0xFE: # TAH_BYTE
            pos += print_type_attr(ti[pos:])
        ret_type = ord(ti[pos])
        print "return type:"
        pos += print_type_info(ti[pos:]) # rettype
        # TODO: <- serialized argloc_t
        if cc == 0xD0 or cc == 0xE0 or cc == 0xF0:
            if (ret_type & 0x3F) is not 1:
                pos += print_argloc(ti[pos:]) # retloc
        if not (cc == 0x20): # not CM_CC_VOIDARG
            N, size = get_dt(ti[pos:])
            pos += size
            print "num_params: {0}".format(N)
            if N == 0:
                # CM_CC_ELLIPSIS or CM_CC_SPECIALE
                if cc == 0x40 or cc == 0xD0:
                    pass # func(...)
                else:
                    pass # params are unknown
            else:
                for i in xrange(N):
                    print "param {0}:".format(i)
                    fah_byte = ord(ti[pos])
                    if fah_byte == 0xFF:
                        flags, tilen = get_de(ti[pos:])
                        pos += tilen
                    pos += print_type_info(ti[pos:])
                    # print place of each param
                    if cc == 0xD0 or cc == 0xE0 or cc == 0xF0:
                        pos += print_argloc(ti[pos:])
        pass
    elif base == 0xD:   # BT_COMPLEX
        #pos += 1
        N, size = get_complex_n(ti[pos:])
        if flags == 0x00:   # BTMT_STRUCT
            pos += size
            if N == 0:
                pos += print_p_string(ti[pos:])
                # TODO: <- parse_sdacl_attr (sdacl?)
                tah_byte = ord(ti[pos])
                if tah_byte == 0xFE:
                    pos += print_type_attr(ti[pos:])
            else:
                ALPOW = N & 0x7
                MCNT = N >> 3
                if ALPOW == 0:
                    print 'alignment: default'
                else:
                    print 'alignment: {0}'.format(1 << (ALPOW-1))
                print "member_count: {0}".format(MCNT)
                # TODO: <- sdacl type attr
                if is_sdacl_byte(ti[pos]):
                    pos += print_type_attr(ti[pos:])
                    '''
                    structure alignment = tah & 0xF
                    ''' 
                # MCNT records: type_t
                for i in xrange(MCNT):
                    print "field {0}:".format(i)
                    tilen = print_type_info(ti[pos:])
                    pos += tilen
                    # sdacl-typeattr
                    if is_sdacl_byte(ti[pos]):
                        pos += print_type_attr(ti[pos:]) # tafld_bits
                        '''
                        tah & 0xF = alignment
                        tah &= 0xFFFFFFF0
                        if tah >> 5 & 1:
                            this struct is TAUDT_CPPOBJ
                        '''
        if flags == 0x10:   # BTMT_UNION
            pos += size
            if N == 0:
                pos += print_p_string(ti[pos:])
                tah_byte = ord(ti[pos])
                if tah_byte == 0xFE:
                    pos += print_type_attr(ti[pos:])
            else:
                ALPOW = N & 0x7
                MCNT = N >> 3
                if ALPOW == 0:
                    print 'alignment: default'
                else:
                    print 'alignment: {0}'.format(1 << (ALPOW-1))
                print "member_count: {0}".format(MCNT)
                # TODO: <- sdacl type attr
                if is_sdacl_byte(ti[pos]):
                    pos += print_type_attr(ti[pos:])
                # MCNT records: type_t
                for i in xrange(MCNT):
                    print "field {0}:".format(i)
                    tilen = print_type_info(ti[pos:])
                    pos += tilen
        if flags == 0x20:   # BTMT_ENUM
            pos += size
            if N == 0:
                pos += print_p_string(ti[pos:])
                tah_byte = ord(ti[pos])
                if tah_byte == 0xFE:
                    pos += print_type_attr(ti[pos:])
            else:
                # TODO: <- tah type attr
                tah_byte = ord(ti[pos])
                if tah_byte == 0xFE:
                    pos += print_type_attr(ti[pos:])
                bte = ord(ti[pos])
                print "member_count: {0}".format(N)
                print_bte(bte)
                pos += 1
                cur = 0
                o = 0
                for i in xrange(N):
                    delta, size = get_de(ti[pos+o:])
                    cur += delta
                    o += size
                    if bte & 0x10:
                        print "mask: {0:08X}".format(delta)
                        F, size = get_complex_n(ti[pos:])
                        pos += size
                        for x in xrange(F):
                            val, tilen = get_de(ti[pos:])
                            pos += tilen
                            print "what is this?: 0x{0:x}".format(val)
                    else:
                        print "index: {0:04x} delta: {1} value: 0x{2:x}".format(i,delta,cur & 0xffffffff)
        if flags == 0x30:   # BTMT_TYPEDEF
            #pos += size
            pos += print_p_string(ti[pos:])
    elif base == 0xE:   # BT_BITFIELD (only in struct or enum)
        dt, tilen = get_dt(ti[pos:])
        print 'nbits: {0}, unsigned {1}'.format(dt >> 1, dt & 1)
        pos += tilen
        tah_byte = ord(ti[pos])
        if tah_byte == 0xFE:
            pos += print_type_attr(ti[pos:])
    print '</type>'

    return pos # returns length of type string

sclass_t = (
    "unknown",
    "typedef",
    "extern",
    "static",
    "register",
    "auto",
    "friend",
    "virtual"
)

def print_type_record(name, type_info, cmt, fields, fieldcmts, sclass):
    #print name
    #print cmt
    #print_p_list(fields)
    #print_p_list(fieldcmts)
    print_type_info(type_info,name)

def process_bucket(bucket):
    buf = io.BufferedReader(io.BytesIO(bucket['buf']))
    
    i = 0
    while i < bucket['ndefs']:
        flags = u32(buf)
        name = c_string(buf)
        #print name

        if flags >> 31:
            ordinal = u64(buf)
        else:
            ordinal = u32(buf)

        if flags != 0x7FFFFFFF and flags != 0xFFFFFFFF:
            raise Exception('unsupported format {0}'.format(buf.tell()))

        type_info = t_string(buf) # type_t[]
        cmt = c_string(buf) # char[]
        fields = c_string(buf) # p_list
        fieldcmts = c_string(buf) # p_list
        sclass = u8(buf)

        if (ord(type_info[0]) & 0x0F) == 0xD:
            print_type_record(name, type_info, cmt, fields, fieldcmts, sclass)
        print ""
        
        i+=1

    print 'end: {0} {1}'.format(bucket['size'], buf.tell())

def process_macros(bucket):
    buf = io.BufferedReader(io.BytesIO(bucket['buf']))

    i = 0
    while i < bucket['ndefs']:
        name = c_string(buf)
        nparams = u8(buf)
        isfunc = u8(buf)
        value = c_string(buf)

        print name

        i+=1

    print 'end: {0} {1}'.format(bucket['size'], buf.tell())

def load_til(filename):
    f = open(filename, 'rb')
    sig = f.read(6)
    format = u32(f)
    flags = u32(f)
    titlelen = u8(f)
    title = f.read(titlelen)
    baselen = u8(f)
    base = f.read(baselen)

    id = f.read(1) # compiler id
    cm = f.read(1) # memory model
    size_i = f.read(1)
    size_b = f.read(1)
    size_e = f.read(1)
    defalign = f.read(1)

    if flags & 0x4:
        size_s = f.read(1)
        size_l = f.read(1)
        size_ll = f.read(1)

    if flags & 0x100:
        size_ldbl = f.read(1)
        
    def load_bucket(f):
        ndefs = u32(f)
        size = u32(f)
        buf = None
        
        if flags & 0x1:
            csize = u32(f)
            buf = zlib.decompress(f.read(csize))
        else:
            buf = f.read(size)
            
        return { 'ndefs': ndefs,
            'size': size,
            'buf': buf }
        
    syms = load_bucket(f)
    types = load_bucket(f)
    macros = load_bucket(f)

    process_bucket(syms)
    process_bucket(types)
    process_macros(macros)
'''
if not sys.argv[1]:
    exit()
else:
    load_til(sys.argv[1])
'''
sys.stdout = open('log.txt', 'w')

load_til('wdk81_um.til')