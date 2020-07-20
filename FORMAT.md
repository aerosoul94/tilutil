# TIL Format
### Header
| Type | Field |
|------|-------|
| char[6] | magic "IDATIL"|
| uint32 | format flags|
| uint32 | flags|
| string | title|
| string | base file name|
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

### Buckets
TODO