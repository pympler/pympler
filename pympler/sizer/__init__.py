
 # check supported Python version
import sys
if getattr(sys, 'hexversion', 0) < 0x2020000:
    raise NotImplementedError('sizer requires Python 2.2 or newer')

from asizeof import *
