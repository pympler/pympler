"""Project metadata.

This information is used in setup.py as well as in doc/source/conf.py.

"""

project_name = 'Pympler'
version      = '0.9'
url          = 'https://github.com/pympler/pympler'
license      = 'Apache License, Version 2.0'
author       = 'Jean Brouwers, Ludwig Haehne, Robert Schuppenies'
author_email = 'pympler-dev@googlegroups.com'
copyright    = '2008-2020, ' + author
description  = ('A development tool to measure, monitor and analyze '
                'the memory behavior of Python objects.')
long_description = '''
Pympler is a development tool to measure, monitor and analyze the
memory behavior of Python objects in a running Python application.

By pympling a Python application, detailed insight in the size and
the lifetime of Python objects can be obtained.  Undesirable or
unexpected runtime behavior like memory bloat and other "pymples"
can easily be identified.

Pympler integrates three previously separate projects into a single,
comprehensive profiling tool. Asizeof provides basic size information
for one or several Python objects, muppy is used for on-line
monitoring of a Python application and the class tracker provides
off-line analysis of the lifetime of selected Python objects. A
web profiling frontend exposes process statistics, garbage
visualisation and class tracker statistics.

Pympler is written entirely in Python, with no dependencies to
external libraries. It has been tested with Python 2.7, 3.5, 3.6,
3.7, 3.8, 3.9 on Linux, Windows and MacOS X.
'''
