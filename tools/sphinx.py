#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    run Sphinx, the Python documentation tool,
    if installed in the current Python build.
    Otherwise try the  sphi.x-build command

    Originals at <http://sphinx.pocoo.org/>
'''

import sys

try:
    from sphinx import main
    sys.exit(main(sys.argv))

except ImportError:
    pass

 # Sphinx not installed in this Python build,
 # try running the original  sphinx-build
import os

os.execlp('sphinx-build', *sys.argv)
