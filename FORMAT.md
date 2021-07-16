# TIL Format

 - [Header](#header)
 - [Buckets](#buckets)
   - [Type Data](#type-data)
     - [Decoding typestrings](#decoding-typestrings)
   - [Macro](#macro)

Here is a list of types used under the "Type" columns for reference.

<table>
    <tr>
        <th>Type</th>
        <th>Description</th>
    </tr>
    <tr>
        <th colspan="2">Integer types</th>
    </tr>
    <tr>
        <td>uint8</td>
        <td>Unsigned 8-bit value</td>
    </tr>
    <tr>
        <td>uint16</td>
        <td>Unsigned 16-bit value</td>
    </tr>
    <tr>
        <td>uint32</td>
        <td>Unsigned 32-bit value</td>
    </tr>
    <tr>
        <td>uint64</td>
        <td>Unsigned 64-bit value</td>
    </tr>
    <tr>
        <th colspan="2">String types</th>
    </tr>
    <tr>
        <td>cstring</td>
        <td>Null terminated string</td>
    </tr>
    <tr>
        <td>pstring</td>
        <td>Pascal string (length prefixed, no terminator byte)</td>
    </tr>
    <tr>
        <td>plist</td>
        <td>Multiple pstring's joined together. The end of the plist is null terminated. Note that there are no separators between pstring's.</td>
    </tr>
    <tr>
        <td>typestring</td>
        <td>Null terminated string that contains encoded type information</td>
    </tr>
</table>

## Header
> :information_source: See the TILHeader class in tilfile.py for implementation

| Type | Field |
|------|-------|
| uint8[6] | magic "IDATIL"|
| uint32 | format flags/version|
| uint32 | flags|
| pstring | title|
| pstring | base file name|
| uint8 | compiler id (see comp_t in typeinfo.hpp)|
| uint8 | memory model (see cm_t in typeinfo.hpp)|
| uint8 | sizeof(int)|
| uint8 | sizeof(bool)|
| uint8 | sizeof(enum)|
| uint8 | default alignment|

This is read only if the `TLD_ESI` flag is set in `flags`.

| Type | Field |
|------|-------|
| uint8 | sizeof(short) |
| uint8 | sizeof(long) |
| uint8 | sizeof(long long) |

This is read after only if the `TLD_SLD` flag is set in `flags`.

| Type | Field |
|------|-------|
| uint8 | sizeof(long double) |

After this header follows 3 [buckets](#buckets) that store type information.

## Buckets
> :information_source: See the TILBucket class in tilfile.py for implementation

A til file has 3 buckets that contain symbols, types, and macros in order. The symbol bucket include typedefs and function signatures, the type bucket includes structs and enums, and the macro bucket contains macro definitions.

A til bucket's header structure depends on the til header's flags. If the `TIL_ORD` is set, then you'll find an extra `uint32` for the number of ordinals at the beginning of the header and if the `TIL_ZIP` then you'll find an extra `uint32` at the end of this header for the compressed size. `TIL_ZIP` also means that the data for all buckets is compressed. After this header follows the compressed or uncompressed type data. The first two buckets, for symbols and types, contain type information structured as [TypeData](#type-data) while the macro bucket contains information structured as [Macro](#macro).

| Type | Field |
|------|-------|
| uint32 | number of ordinals (this field only exists if `TIL_ORD` is set) |
| uint32 | number of definitions |
| uint32 | size of uncompressed data |
| uint32 | size of compressed data (this field only exists if `TIL_ZIP` is set) |

### Type Data
> :information_source: See the TypeData class in tilfile.py for implementation

This data is present in both the symbol and type buckets (first and second). There is one of these per symbol/type.

| Type | Field |
|------|-------|
| uint32 | type flags (this needs more research) |
| cstring | name |
| uint32 or uint64 | ordinal (size depends on type flags) |
| typestring | contains this type's encoded information |
| cstring | type comment |
| plist | fields |
| plist | field comments |
| uint8 | sclass |

#### Decoding typestrings
> :information_source: See TypeString class in tilfile.py for implementation

> :information_source: See all deserialize methods in datatypes.py

TODO

### Macro
> :information_source: See the Macro class in tilfile.py for implementation

This data is present in both the macro bucket. There is one of these per macro.

| Type | Field |
|------|-------|
| cstring | name |
| u8 | number of arguments |
| u8 | is function? (boolean) |
| cstring | value; or expression where arguments are replaced with indexes |