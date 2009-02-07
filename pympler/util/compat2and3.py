"""
Compatibility layer to allow Pympler being used from Python 2.x and Python 3.x.
"""

import sys

# Version dependent imports

try:
    from StringIO import StringIO
    BytesIO = StringIO
except ImportError:
    from io import StringIO, BytesIO

try:
    from new         import instancemethod
except ImportError: # Python 3.0
    def instancemethod(*args):
        return args[0]

# Helper functions

# Python 2.x expects strings when calling communicate and passing data via a
# pipe while Python 3.x expects binary (encoded) data. The following works with
# both:
#
#   p = Popen(..., stdin=PIPE)
#   p.communicate(encode4pipe("spam"))
#
encode4pipe = lambda s: s
if sys.hexversion >= 0x3000000:
    encode4pipe = lambda s: s.encode()
