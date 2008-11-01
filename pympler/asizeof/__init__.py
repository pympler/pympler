
_M = 'asizeof'
_P = 'pympler.' + _M

import sys
if sys.hexversion < 0x2020000:
    raise NotImplementedError('%s requires Python 2.2 or newer' % _P)

 # lift all module attrs into this package such that
 # importing this package is equivalent to importing
 # all modules inside this package without exposing
 # any of the modules and structure of the package
p = sys.modules.get(_P, None)  # this package

 # using 'from _M import *' fails with Python 3.0 and
 # Python 2.x raises SyntaxError for 'from ._M import *'
m = __import__(_M, globals())
if m and m != p:
     # replace this package with the (single) module
    sys.modules[_P] = m
else:
    raise ImportError('import %s as %s failed' % (_M, _P))

if sys.hexversion < 0x3000000:  # for Python 2.x only
     # remove all empty sys.modules entries created
     # as side effects of the __import__ call above
    _P += '.'
    for n in [n for n, m in sys.modules.iteritems()
                    if m is None and n.startswith(_P)]:
        del sys.modules[n]
    del n
del _M, m, _P, p  # clean up
