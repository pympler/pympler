#! /usr/bin/env python

import glob
import os
import struct
import sys
import unittest

_glob_test_py = 'test_*.py'

if os.linesep == '\n':
    def _print(text):
        print(text)
else:
    def _print(text):
        print(text.replace('\n', os.linesep))

def get_tests(dir='.', clean=False):
    '''Get a list of test module names in the given directory.
    '''
    res, dir_ = [], ''
     # walk recursively through all subdirectories
    if os.path.isdir(dir):
        if dir != '.':
           dir_ = dir.rstrip(os.sep) + os.sep
        for sub in os.listdir(dir):
            if sub[0] != '.':  # os.curdir
               sub = dir_ + sub
               if os.path.isdir(sub):
                   res.extend(get_tests(sub))
        glob_py = dir_ + _glob_test_py
    elif os.path.isfile(dir):
        glob_py = dir
        sub = os.path.split(dir)[0]
        if sub:  # prefix
            dir_ = sub + os.sep
    else:
        return res
     # append all tests as module names
    for test in glob.glob(glob_py):
        test = dir_ + os.path.basename(test)
        if clean:  # remove existing bytecodes
            for co in ('c', 'o'):
                try:
                    os.remove(test + co)
                except OSError:
                    pass
         # convert to module name and remove leading ./ or .\
        test = test[:-3].replace(os.sep, '.')
        test = test.lstrip('.')
        res.append(test)
    res.sort(key=lambda s: -s.count('test_tracker'))
    return res  # sorted(res)

def suite(dirs=['.'], clean=False, pre=True, verbose=2):
    '''Create a suite with all tests from the given directories.

    This will also include tests from subdirectories.
    '''
    all = True
    res = unittest.TestSuite()
    for dir in dirs:
        for test in get_tests(dir, clean):
            # Import tests relative to 'test' directory
            test = test[test.find('.')+1:]
            try:
                mod = test.rfind('.') + 1
                if mod > 0:  # from test import mod
                   mod = test[mod:]
                   mod = __import__(test, globals(), locals(), [mod])
                else:  # import test
                   mod = __import__(test)
                res.addTest(unittest.defaultTestLoader.loadTestsFromModule(mod))
            except ImportError:
                if sys.hexversion < 0x02050000:
                   _print('Warning: ignoring %r - incompatible with this Python version' % test)
                else:
                    raise
            except (SyntaxError, NameError):
                if pre:
                   _print('Warning: ignoring %r due to an error while importing' % test)
                else:
                   _print('Error: %r missing or not found' % test)
                if verbose > 2:
                    raise  # show the error
                all = False
    return res, all


if __name__ == '__main__':

     # default values for options
    clean   = False  # -c[lean]  -- remove all .pyo and .pyc files
    pre     = True   # -pre[-install]  -- try before installation
   #pre     = False  # -post[-install]  -- test after installation
    verbose = 2      # -v[erbose] <level>  -- verbosity level

     # get options and test case directories (files?)
    dirs = sys.argv[1:]
    while dirs:
        t = dirs[0]
        n = len(t)
        if '-clean'.startswith(t) and n > 1:
            clean = True
        elif '-post-install'.startswith(t) and n > 4:
            pre = False
        elif '-pre-install'.startswith(t) and n > 3:
            pre = True
        elif '-verbose'.startswith(t) and n > 1:
            verbose = int(dirs.pop(1))
        else:
            break
        dirs = dirs[1:]
    else:
        dirs = ['.']

    # Insert parent directory such that the code modules can be
    # imported, but only for pre-install testing. Import test directory
    # for pre and post-install testing.
    t = os.path.split(sys.path[0])
    if t and pre:
        sys.path.insert(1, t[0])
    sys.path.append(os.path.join(t[0], 'test'))

     # print some details
    if verbose > 1:
        t = '%d-bit [' % (struct.calcsize('P') << 3)
        _print('Python %s\n' % sys.version.replace('[', t))
        if verbose > 4:
            t = '\n          '  # indentation
            _print('Sys.path: %s\n' % t.join(sys.path))
        if verbose > 3:
            _print('Test dirs: %r\n' % dirs)

     # build and run single test suite
    tst, all = suite(dirs, clean=clean, pre=pre, verbose=verbose)
    if pre or all:
        res = unittest.TextTestRunner(verbosity=verbose).run(tst)
        if res.wasSuccessful():
            sys.exit(0)
    sys.exit(1)
