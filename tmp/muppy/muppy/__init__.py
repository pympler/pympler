"""Tool set for measuring the memory usage of Python applications.

Be aware that muppy will call gc.collect() whenever the object state is
gathered to remove reference cycles.

"""

__all__ = ['refbrowser',
           'refbrowser_gui',
           'tracker',
           'summary']

from muppy import *

def print_summary():
    """Print a summary of all known objects."""
    summary.print_(summary.summarize(get_objects()))

