#!/usr/bin/env python

import os
import sys
import re

from optparse import OptionParser

_Python_path = sys.executable  # this Python binary

try:
    from subprocess import call as _call

    def _spawn(*args):
        '''Run command in sub-process.
        '''
        return _call(args)

except ImportError:
    def _spawn(arg0, *args):
        '''Run command in sub-process.
        '''
        return os.spawnlp(os.P_WAIT, arg0, arg0, *args)

def get_files(locations=['test'], pattern='^test_[^\n]*.py$'):
    '''Return all matching files in the given locations.

    From the given directory locations recursively get all files
    matching the specified name pattern.  Any locations which are
    file names and match the name pattern are returned verbatim.
    '''
    res = []
    pat = re.compile(pattern)
    for location in locations:
        if os.path.isfile(location):
            fn = os.path.basename(location)
            if pat.match(fn):
                res.append(location)
        elif os.path.isdir(location):
            for root, dirs, files in os.walk(location):
                for fn in files:
                    if pat.match(fn):
                        res.append(os.path.join(root,fn))
    return res

def run_unittests(project_path, dirs=[], verbose=2):
    '''Run unittests for all given test directories.

    If no tests are given, all unittests will be executed.
    '''
    os.environ['PYTHONPATH'] = project_path
    _spawn(_Python_path,  # use this Python binary
           os.path.join('test', 'runtest.py'),
           '-verbose', str(verbose),
           *dirs)

def run_pychecker(dirs, OKd=False, verbose=1):
    '''Run PyChecker against all specified source files and/or
    directories.

    PyChecker is invoked thru the  tools/pychok postprocessor to
    suppressed all warnings OK'd in the source code.
    '''
    no_OKd = {False: '-no-OKd', True: '--'}[OKd]
    sources = get_files(dirs, pattern='[^\n]*.py$')
    for src in sources:
        if verbose > 0:
            print ("CHECKING %s ..." % src)
        _spawn(_Python_path,  # use this Python binary
               'tools/pychok.py', no_OKd,
               '--stdlib', '--quiet',
                src)

def run_docs(path, actions=['html', 'doctest']):
    '''Test documentation with sphinx.

    Possible entries for the actions list are all valid parameters
    for the 'make' command inside the documentation directory.
    '''
    cwd = os.getcwd()
    os.chdir(path)
    for action in actions:
        _spawn('make', 'clean')
        _spawn('make',  action)
        _spawn('make', 'clean')
    os.chdir(cwd)

def print2(text, verbose=1):
    '''Print a headline text.
    '''
    if verbose > 0:
        print ('')
        if text:
            print (text)
            print ('=' * len(text))

def main():
    '''
    Find and run all specified tests.
    '''
    usage = "usage: %prog <options> [test | test/module | test/module/test_suite.py ...]"
    parser = OptionParser(usage)
    parser.add_option('-a', '--all', action='store_true', default=False,
                      dest='all', help='run all tests and docs.')
    parser.add_option('-d', '--doctest', action='store_true', default=False,
                      dest='doctest', help='run the documentation tests.')
    parser.add_option('-H', '--html', action='store_true', default=False,
                      dest='html', help='create the HTML documentation.')
    parser.add_option('-P', '--pychecker', action='store_true', default=False,
                      dest='pychecker', help='run static code analyser PyChecker')
    parser.add_option('--OKd', action='store_true', default=False,
                      dest='OKd', help='include OKd PyChecker warnings')
    parser.add_option('-v', '--verbose', default=2,
                      dest='V', help='set verbosity level for unit tests (2)')
    parser.add_option('-t', '--test', action='store_true', default=False,
                      dest='test', help='run all or the specified unit tests')
    (options, args) = parser.parse_args()

    project_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    test_path = os.path.join(project_path, 'test')
    doc_path = os.path.join(project_path, 'doc')

    if options.all:
        options.html = True
        options.doctest = True
        options.test = True
        options.pychecker = True

    if options.pychecker:
        print2('Running pychecker', options.V)
        run_pychecker(args or ['pympler'], options.OKd, options.V)

    if options.html:
        print2('Creating documention', options.V)
        run_docs(doc_path, actions=['html'])

    if options.doctest:
        print2('Running doctest', options.V)
        run_docs(doc_path, actions=['doctest'])

    if options.test:
        print2('Running unittests', options.V)
        run_unittests(project_path, args or ['test'], options.V)


if __name__ == '__main__':
    main()
