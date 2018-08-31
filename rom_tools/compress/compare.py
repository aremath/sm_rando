from util import *
from compress import *
from decompress import *

# Verify that Lunar decompression corresponds to raw:
#   a -> me -> c -> lunar -> a
d = filediffs("testing/raw.b", "testing/lunarraw.b")
assert len(d) == 0, str(d)

# Verify that my decompression of Lunar compression corresponds to raw
#   a -> lunar -> c -> me -> a
c = bytes_from_file("testing/lunarpress.b")
dc = decompress(c)
src = bytes_from_file("testing/raw.b")
d = differs(src, dc)
assert len(d) == 0, str(d)
