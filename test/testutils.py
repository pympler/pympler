"""
Base functionality for Pympler tests.
"""

import sys


def disable(func):
    """
    Decorator to deactivate a test method.
    The test is still run if the test module is invoked directly.
    """

    def _exclude(self, *args, **kwargs):
        if 'runtest.py' in sys.argv[0]:
            sys.stderr.write("(disabled) ")
        else:
            func(self, *args, **kwargs)

    return _exclude
