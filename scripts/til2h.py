from til.tilfile import TIL
import sys


def dump(tilname, header):
    with open(tilname, "rb") as fp, open(header, "w") as op:
        print("Loading {}...".format(tilname))
        til = TIL(fp)
        print("Finished Loading.")

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
            data = tinfo.print_type(sym.get_name())
            if data:
                op.write(data)

        for typ in til.get_types():
            tinfo = typ.get_type_info()
            data = tinfo.print_type(typ.get_name())
            if data:
                op.write(data)

        for macro in til.get_macros():
            op.write(macro.print_type())


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: {} <til file> <header file>".format(sys.argv[0]))
        exit()
    dump(sys.argv[1], sys.argv[2])
