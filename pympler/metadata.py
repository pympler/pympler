"""Project metadata.

This information is used in setup.py as well as in doc/source/conf.py.

"""

project_name = 'Pympler'
version      = '0.2.0'
url          = 'http://packages.python.org/Pympler/'
license      = 'Apache License, Version 2.0' #PYCHOK valid
author       = 'Jean Brouwers, Ludwig Haehne, Robert Schuppenies'
author_email = 'pympler-dev@googlegroups.com'
copyright    = '2008-2009, ' + author #PYCHOK valid
description  = ('A development tool to measure, monitor and analyze '
                'the memory behavior of Python objects.')
long_description = '''
Pympler is a development tool to measure, monitor and analyze the
memory behavior of Python objects in a running Python application.

By pympling a Python application, detailed insight in the size and
the lifetime of Python objects can be obtained.  Undesirable or
unexpected runtime behavior like memory bloat and other "pymples"
can easily be identified.

Pympler integrates three previously separate modules into a single,
comprehensive profiling tool.  The  asizeof module provides basic
size information for one or several Python objects, module  muppy
is used for on-line monitoring of a Python application and module
tracker provides off-line analysis of the lifetime of selected
Python objects.

Pympler is written entirely in Python, with no dependencies other
than standard Python modules and libraries.  All Pympler modules
work with Python 2.4, 2.5 and 2.6.  Module  asizeof has also been
tested with Python 2.2, 2.3 and 3.0 on a number of Linux distros,
MacOS X (10.4.11 Intel and 10.3.9 PPC), Solaris 10 (Opteron) and
Windows XP with 32-bit and several 64-bit Python builds.
'''
