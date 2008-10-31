"""Toolset for measuring the memory usage of Python applications.

Be aware that muppy will call gc.collect() whenever the object state is
gathered to remove reference cycles.

"""
import sys
version = sys.version[0] + sys.version[2]
if int(version) < 24:
    raise NotImplementedError('muppy requires Python 2.4 or newer.')

__all__ = ['refbrowser',
           'refbrowser_gui',
           'tracker',
           'summary']

from muppy import *

def print_summary():
    """Print a summary of all known objects."""
    summary.print_(summary.summarize(get_objects()))

