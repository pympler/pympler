#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Run Sphinx, the Python documentation tool.

   First try running Sphinx installed in the current
   Python build.  If that fails, try the standard
   ``sphinx-build`` command which may be installed in
   a different Python version.  If that fails, punt.

   Originals at *http://sphinx.pocoo.org/*.
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
