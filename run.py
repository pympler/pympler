#!/usr/bin/env python

import os
import struct
import sys
import re

from optparse import OptionParser

_Python_path = sys.executable  # this Python binary
_Src_dir     = 'pympler'
_Verbose     = 1

try:
    from distutils.dir_util import mkpath as _mkpath
except ImportError:
    def _mkpath(dir, **unused):
        try:
            os.makedirs(dir)
        except OSError:  # dir exists
            pass
        return dir  # like distutils

from shutil import move as _mv, rmtree as shutil_rmtree

def _rmtree(dir):
     # unlike dist_utils.dir_util.remove_tree,
     # shutil.rmtree does ignore all errors
    shutil_rmtree(dir, True)

try:
    from subprocess import call as _call
  ##from distutils.spawn import spawn as _call  # raises DistutilsExecError
    def _spawn(*args):
        '''Run command in sub-process.
        '''
        if _Verbose > 2:
            print('Spawning: %s' % ' '.join(args))
        return _call(args)
except ImportError:
    def _spawn(arg0, *args):
        '''Run command in sub-process.
        '''
        if _Verbose > 2:
            print('Spawning: %s %s' % (arg0, ' '.join(args)))
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

def run_dist(project_path, formats=[]):
    '''Create the distributions.
    '''
    f = ','.join(formats) or []
    if f:
       f = ['--formats=%s' % f]
    os.environ['PYTHONPATH'] = project_path
    _spawn(_Python_path,  # use this Python binary
           'setup.py', 'sdist',
           '--force-manifest',
           *f)

def run_pychecker(dirs, OKd=False):
    '''Run PyChecker against all specified source files and/or
    directories.

    PyChecker is invoked thru the  tools/pychok postprocessor
    to suppresse all warnings OK'd in the source code.
    '''
    no_OKd = {False: '-no-OKd', True: '--'}[OKd]
    sources = get_files(dirs, pattern='[^\n]*.py$')
    for src in sources:
        if _Verbose > 0:
            print ("Checking %s ..." % src)
        _spawn(_Python_path,  # use this Python binary
               'tools/pychok.py', no_OKd,
               '--stdlib', '--quiet',
                src)

def run_sphinx(doc_path, builders=['html', 'doctest'], keep=False, paper=''):
    '''Create and test documentation with Sphinx.
    '''
     # find the  sphinx-build script for
     # Sphinx installed in this Python
    for bin in (os.path.join(sys.exec_prefix, 'bin'), sys.exec_prefix,
                os.path.join(sys.prefix, 'bin'), sys.prefix,
                os.path.split(_Python_path)[0]):
        sphinx = os.path.join(bin, 'sphinx-build')
        if os.access(sphinx, os.X_OK):
            break
    else:  # maybe ./doc/sphinx-build.py
        sphinx = 'sphinx-build.py'
    if _Verbose > 1:
        print ("Using %r ..." % sphinx)
     # change to ./doc dir
    cwd = os.getcwd()
    os.chdir(doc_path)
    doctrees = os.path.join('build', 'doctrees')
    for builder in builders:
        _rmtree(doctrees)
        _mkpath(doctrees)
        dir = os.path.join('build', builder)
        _rmtree(dir)
        _mkpath(dir)
         # see  sphinx-build.py -help
        opts = '-d', doctrees
        if not keep:
            opts += '-q',  # only warnings, no output
        if paper:  # 'letter' or 'a4'
            opts += '-D', ('latex_paper_size=%s' % paper)
        opts += 'source', dir  # source and out dirs
        _spawn(_Python_path,  # use this Python binary
               sphinx,  # to run its Sphinx script
               '-b', builder, *opts)
        if keep:  # move dir up
            _rmtree(builder)
            _mv(dir, builder)  # os.curdir
        else:
            _rmtree(dir)
    _rmtree(doctrees)
    os.chdir(cwd)

def run_unittests(project_path, dirs=[]):
    '''Run unittests for all given test directories.

    If no tests are given, all unittests will be executed.
    '''
     # run the tests using  test/runtest.py *dirs
    _spawn(_Python_path,  # use this Python binary
            os.path.join('test', 'runtest.py'),
           '-verbose', str(_Verbose + 1),
           '-clean', '-pre', *dirs)

def print2(text):
    '''Print a headline text.
    '''
    if _Verbose > 0:
        print ('')
        if text:
            b =  struct.calcsize('P') << 3
            p =  sys.version.split()[0]
            t = '%s (%d-bit Python %s)' % (text, b, p)
            print (t)
            print ('=' * len(t))

def main():
    '''
    Find and run all specified tests.
    '''
    usage = ('usage: %prog <options> [<args> ...]', '',
             '  e.g. %prog --dist [gztar] [zip]',
             '       %prog --doctest',
             '       %prog --html [--keep]',
             '       %prog --latex [--paper=letter|a4]',
           ('       %%prog --pychecker [--OKd] [%s | %s/module] ...' % (_Src_dir, _Src_dir)),
             '       %prog --test [test | test/module | test/module/test_suite.py ...]')
    parser = OptionParser(os.linesep.join(usage))
    parser.add_option('-a', '--all', action='store_true', default=False,
                      dest='all', help='run all tests and create all documentations')
    parser.add_option('-c', '--clean', action='store_true', default=False,
                      dest='clean', help='remove bytecode files from source and test directories')
    parser.add_option('-d', '--dist', action='store_true', default=False,
                      dest='dist', help='create the distributions')
    parser.add_option('-D', '--doctest', action='store_true', default=False,
                      dest='doctest', help='run the documentation tests')
    parser.add_option('-H', '--html', action='store_true', default=False,
                      dest='html', help='create the HTML documentation')
    parser.add_option('-k', '--keep', action='store_true', default=False,
                      dest='keep', help='keep documentation in the doc directory')
    parser.add_option('-L','--latex', action='store_true', default=False,
                      dest='latex', help='create the LaTeX (PDF) documentation')
    parser.add_option('--paper', default='letter',  # or 'a4'
                      dest='paper', help='select LaTeX paper size (letter)')
    parser.add_option('-i', '--linkcheck', action='store_true', default=False,
                      dest='linkcheck', help='check the documentation links')
    parser.add_option('-p', '--pychecker', action='store_true', default=False,
                      dest='pychecker', help='run static code analyzer PyChecker')
    parser.add_option('--OKd', action='store_true', default=False,
                      dest='OKd', help='include PyChecker warnings OKd in source')
    parser.add_option('-V', '--verbose', default='1',
                      dest='V', help='set verbosity level (1)')
    parser.add_option('-t', '--test', action='store_true', default=False,
                      dest='test', help='run all or specific unit tests')
    (options, args) = parser.parse_args()

    project_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    test_path = os.path.join(project_path, 'test')
    doc_path = os.path.join(project_path, 'doc')

    os.environ['PYTHONPATH'] = os.pathsep.join([project_path,
                                               #os.path.join(project_path, _Src_dir),
                                                os.environ.get('PYTHONPATH', '')])
    global _Verbose
    _Verbose = int(options.V)

    if options.all:
        options.clean = True
        options.doctest = True
        options.html = True
        options.keep = True
        options.linkcheck = True
        options.test = True
        options.pychecker = True

    if options.clean or options.dist:  # remove all bytecodes, first
        codes = get_files([_Src_dir, 'test'], pattern='[^\n]*.py[c,o]$')
        for code in codes:
            if _Verbose > 1:
                print ("Removing %r ..." % code)
            os.remove(code)

    if options.pychecker:
        print2('Running pychecker')
        run_pychecker(args or [_Src_dir], options.OKd)

    if options.doctest:
        print2('Running doctest')
        run_sphinx(doc_path, ['doctest'])

    if options.html:
        print2('Creating HTML documention')
        run_sphinx(doc_path, ['html'], keep=options.keep)

    if options.latex:
        print2('Creating LaTex (PDF) documention')
        run_sphinx(doc_path, ['latex'], paper=options.paper)

    if options.linkcheck:
        print2('Checking documention links')
        run_sphinx(doc_path, ['linkcheck'])

    if options.test:
        print2('Running unittests')
        run_unittests(project_path, args or ['test'])

    if options.dist:
        print2('Creating distribution')
        run_dist(project_path, args or ['gztar', 'zip'])


if __name__ == '__main__':
    main()
