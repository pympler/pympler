"""Project metadata.

This information is used in setup.py as well as in doc/source/conf.py.

"""
import inspect
import os

project_name = 'pympler'
version      = '0.1a1'
url          = 'http://packages.python.org/pympler/'
license      = 'Apache License, Version 2.0' #PYCHOK valid
author       = 'Jean Brouwers, Ludwig Haehne, Robert Schuppenies'
author_email = 'pympler-dev@googlegroups.com'
copyright    = '2008, ' + author #PYCHOK valid
description  = ('A development tool to measure, monitor and analyze the '
'memory behavior of Python objects.')
long_description = '\n'
# location of this very module
_modulepath = os.path.abspath(os.path.dirname(inspect.getfile(lambda foo:foo)))
introfile = open(os.path.join(_modulepath, '..', 'doc', 'source', 'intro.rst'))
while 1:
    line = introfile.readline()
    if not line:
        break
    long_description += line

