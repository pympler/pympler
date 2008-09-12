"""Project metadata.

This information is used in setup.py as well as in doc/source/conf.py.

"""
project_name = 'pympler'
version      = '0.1a1'
url          = 'http://packages.python.org/pympler/'
license      = 'Apache License, Version 2.0'

description      = ('A development tool to measure, monitor and analyze the '
'memory behavior of Python objects.')
# read long_description from docs
long_description = '\n'
file = open('doc/source/intro.rst')
while 1:
    line = file.readline()
    if not line:
        break
    long_description += line

author       = 'Jean Brouwers, Ludwig Haehne, Robert Schuppenies'
author_email = 'pympler-dev@googlegroups.com'

copyright    = '2008, ' + author
