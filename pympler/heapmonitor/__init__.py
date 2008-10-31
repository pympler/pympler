
_M = 'heapmonitor'
_P = 'pympler.' + _M

import sys
if sys.hexversion < 0x2040000:
    raise NotImplementedError('%s requires Python 2.4 or newer' % _P)

 # lift all module attrs into this package such that
 # importing this package is equivalent to importing
 # all modules inside this package without exposing
 # any of the modules and structure of the package
p = sys.modules.get(_P, None)  # this package

 # using 'import <_M> as m' fails with Python 3.0 and
 # Python 2.x raises SyntaxError for 'import .<_M> as m'
m = __import__(_M, globals())
if m and m != p and p:
     # replace this package with the (single) module
    sys.modules[_P] = m
else:
    raise ImportError(_P)

if sys.hexversion < 0x3000000:  # for Python 2.x only
     # remove all empty sys.modules entries
    for n, m in sys.modules.items():
        if m is None:
            del sys.modules[n]
    del n

del m, _M, p, _P

