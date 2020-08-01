from til.tilfile import TIL
import sys


def dump(tilname, header):
    with open(tilname, "rb") as fp, open(header, "w") as op:
        print(f"Loading {tilname}...")
        til = TIL(fp)
        print(f"Finished Loading.")

        # Usage in IDA
        # typedata = ida_typeinf.get_named_type(til, name, 0)
        # # returns (code, type_str, fields, cmt, field_cmts, sclass, value)
        # tinfo = ida_typeinf.tinfo_t()
        # typestr = datatype[1]
        # fieldstr = datatype[2]
        # tinfo.deserialize(None, typestr, fieldstr)
        # print(tinfo)

        # Print out all data types
        for sym in til.get_syms():
            tinfo = sym.get_type_info()
            data = tinfo.print(sym.get_name())
            if data:
                op.write(data)

        for typ in til.get_types():
            tinfo = typ.get_type_info()
            data = tinfo.print(typ.get_name())
            if data:
                op.write(data)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <til file> <header file>")
        exit()
    dump(sys.argv[1], sys.argv[2])