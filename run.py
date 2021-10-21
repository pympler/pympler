#!/usr/bin/env python

import os
import struct
import sys

from fnmatch import fnmatch
from optparse import OptionParser

_Python_path =  sys.executable  # this Python binary
_Coverage    = 'python-coverage'
_Src_dir     = 'pympler'
_Verbose     =  1

try:
    from subprocess import call as _call
except ImportError:  # no  subprocess.call
    def _call(args):  # use partial substitute
        return os.spawnlp(os.P_WAIT, args[0], args[0], *args[1:])

def _mkpath(dir, **unused):
    try:
        os.makedirs(dir)
    except OSError:  # dir exists
        pass
    return dir

from shutil import move as _mv, rmtree as shutil_rmtree

def _rmtree(dir):
     # unlike dist_utils.dir_util.remove_tree,
     # shutil.rmtree does ignore all errors
    shutil_rmtree(dir, True)

def get_files(locations=['test'], pattern='test_*.py'):
    '''Return all matching files in the given locations.

    From the given directory locations recursively get all files
    matching the specified name pattern.  Any locations which are
    file names and match the name pattern are returned verbatim.
    '''
    res = []
    for location in locations:
        if os.path.isfile(location):
            fn = os.path.basename(location)
            if fnmatch(fn, pattern):
                res.append(location)
        elif os.path.isdir(location):
            for root, dirs, files in os.walk(location):
                for fn in files:
                    if fnmatch(fn, pattern):
                        res.append(os.path.join(root,fn))
    return res

def run_clean(*dirs):
    '''Remove all bytecode files from the given directories.
    '''
    codes = get_files(dirs, pattern='*.py[c,o]')
    codes.extend(get_files(dirs, pattern='*.py,cover'))
    for code in codes:
        if _Verbose > 1:
            print ("Removing %r ..." % code)
        os.remove(code)

def run_command(*args):
    '''Run a command in sub-process.
    '''
    if _Verbose > 2:
        print('Running: %s' % ' '.join(args))
    r = _call(args)
    if r:
        print("Running '%s ...' failed with exit status %r" % (' '.join(args[:2]), r))
    return r

def run_dist(project_path, formats=[], upload=False):
    '''Create the distributions.
    '''
    f = ','.join(formats) or []
    if f:
       f = ['--formats=%s' % f]
    if upload:
       f.append('upload')
    os.environ['PYTHONPATH'] = project_path
    run_command(_Python_path,  # use this Python binary
                'setup.py', 'sdist',
                '--force-manifest', *f)

def zip_docs(path, target):
    '''Zip the documentation to be uploaded to the Cheeseshop.
    Compress all files found in `path` recursively and strip the leading path
    component. The file is written to `target`.
    '''
    import zipfile
    import glob

    def _strippath(file, path=path):
        return file[len(path)+len(os.sep):]

    zip = zipfile.ZipFile(target, 'w')
    for name in glob.glob(os.path.join(path,'*')):
        if os.path.isdir(name):
            for dirpath, dirnames, filenames in os.walk(name):
                for fname in filenames:
                    file = os.path.join(dirpath, fname)
                    if _Verbose > 1:
                        print ("Add " + _strippath(file))
                    zip.write(file, _strippath(file), zipfile.ZIP_DEFLATED)
        else:
            if _Verbose > 1:
                print ("Add " + _strippath(name))
            zip.write(name, _strippath(name), zipfile.ZIP_DEFLATED)
    zip.close()


def run_sphinx(project_path, builders=['html', 'doctest'], keep=False, paper=''):
    '''Create and test documentation with Sphinx.
    '''
     # change to ./doc dir
    os.chdir(os.path.join(project_path, 'doc'))
    doctrees = os.path.join('build', 'doctrees')
    for builder in builders:
        _rmtree(doctrees)
        _mkpath(doctrees)
        bildir = os.path.join('build', builder)
        _rmtree(bildir)
        _mkpath(bildir)
         # see _Sphinx_build -help
        opts = '-d', doctrees
        if _Verbose == 0:
            opts += '-q',  # only warnings, no output
        if paper:  # 'letter' or 'a4'
            opts += '-D', ('latex_paper_size=%s' % paper)
        opts += 'source', bildir  # source and out dirs
        run_command(_Python_path,  # use this Python binary
                    os.path.join(project_path, 'tools', 'sphinx.py'),
                    '-b', builder, *opts)
        if keep:  # move bildir up
            _rmtree(builder)
            _mv(bildir, builder)  # os.curdir
            zip_docs(builder, os.path.join('..', 'dist', 'pympler-docs.zip'))
        else:
            _rmtree(bildir)
    _rmtree(doctrees)
    os.chdir(project_path)

def run_unittests(project_path, dirs=[], coverage=False):
    '''Run unittests for all given test directories.

    If no tests are given, all unittests will be executed.
    '''
     # run unittests using  test/runtest.py *dirs
    if not coverage:
        run_command(_Python_path,  # use this Python binary
                    os.path.join(project_path, 'test', 'runtest.py'),
                    '-verbose', str(_Verbose + 1),
                    '-clean', '-pre', *dirs)
    else:
        run_command(_Coverage, '-x',  # use installed coverage tool
                    os.path.join(project_path, 'test', 'runtest.py'),
                    '-verbose', str(_Verbose + 1),
                    '-clean', '-pre', *dirs)
        # get all modules from pympler source, print summary and make a copy of
        # each source module with coverage information (mod.py => mod.py,cover)
        mods = get_files(locations=[_Src_dir], pattern='*.py')
        run_command(_Coverage, '-r', *mods) # report
        run_command(_Coverage, '-a', *mods) # annotate

        coverage_out_file = '.coverage'
        if (os.path.exists(coverage_out_file) and
            not os.path.isdir(coverage_out_file)):
            os.unlink(coverage_out_file)

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
    global _Verbose
    global _Coverage

    usage = ('usage: %prog <options> [<args> ...]', '',
             '  e.g. %prog --clean',
             '       %prog --dist [--upload] [gztar] [zip]',
             '       %prog --doctest',
             '       %prog --html [--keep]',
             '       %prog --latex [--paper=letter|a4]',
             '       %prog --linkcheck',
             '       %prog --test [test | test/module | test/module/test_suite.py ...]')
    parser = OptionParser(os.linesep.join(usage))
    parser.add_option('-a', '--all', action='store_true', default=False,
                      dest='all', help='run all tests and create all documentation')
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
    parser.add_option('-t', '--test', action='store_true', default=False,
                      dest='test', help='run all or specific unit tests')
    parser.add_option('--coverage', action='store_true', default=False,
                      dest='coverage', help='collect test coverage statistics')
    parser.add_option('--cov-cmd', default=_Coverage, dest='covcmd',
                      help='coverage invocation command (%s)' % _Coverage)
    parser.add_option('--upload', action='store_true', default=False,
                      dest='upload', help='upload distributions to the Python Cheese Shop')
    parser.add_option('-V', '--verbose', default='1',
                      dest='V', help='set verbosity level (%d)' % _Verbose)
    (options, args) = parser.parse_args()

    project_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    os.environ['PYTHONPATH'] = os.pathsep.join([project_path,
                                               #os.path.join(project_path, _Src_dir),
                                                os.environ.get('PYTHONPATH', '')])
    _Verbose = int(options.V)
    _Coverage = options.covcmd

    if options.all:
        options.clean = True
        options.doctest = True
        options.html = True
        options.keep = True
        options.linkcheck = True
        options.test = True

    if options.clean or options.dist:  # remove all bytecodes, first
        run_clean(_Src_dir, 'test')

    if options.doctest:
        print2('Running doctest')
        run_sphinx(project_path, ['doctest'])

    if options.html:
        print2('Creating HTML documentation')
        run_sphinx(project_path, ['html'], keep=options.keep)

    if options.latex:
        print2('Creating LaTex (PDF) documentation')
        run_sphinx(project_path, ['latex'], paper=options.paper)

    if options.linkcheck:
        print2('Checking documentation links')
        run_sphinx(project_path, ['linkcheck'])

    if options.test:
        print2('Running unittests')
        run_unittests(project_path, args or ['test'], coverage=options.coverage)

    if options.dist:
        print2('Creating distribution')
        run_dist(project_path, args or ['gztar', 'zip'], upload=options.upload)

if __name__ == '__main__':
    main()
