#! /usr/bin/env python

import glob
import os
import struct
import sys
import unittest

_glob_test_py = 'test_*.py'

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
#   elif dir[-3:] == '.py':
#       glob_py = dir
#       sub = os.path.split(dir)[0]
#       if sub:  # prefix
#           dir_ = sub + os.sep
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
         # convert to module name
        test = test[:-3].replace(os.sep, '.')
        res.append(test)
    return res  # sorted(res)

def suite(dirs=['.'], clean=False, verbose=2):
    '''Create a suite with all tests from the given directories.

    This will also include tests from subdirectories.
    '''
    res = unittest.TestSuite()
    for dir in dirs:
        for test in get_tests(dir, clean):
            try:
                mod = test.rfind('.') + 1
                if mod > 0:  # from test import mod
                   mod = test[mod:]
                   mod = __import__(test, globals(), locals(), [mod])
                else:  # import test
                   mod = __import__(test)
                res.addTest(unittest.defaultTestLoader.loadTestsFromModule(mod))
            except (SyntaxError, NameError, ImportError):
                print('WARNING: Ignoring %r due to an error while importing' % test)
                if verbose > 2:
                    raise  # show the error
    return res


if __name__ == '__main__':

     # get -clean and -verbose <level> options
     # and the test case directories (files?)
    clean, verbose, dirs = False, 3, sys.argv[1:]
    while dirs:
        t = dirs[0]
        if '-clean'.startswith(t):
            clean = True
        elif '-verbose'.startswith(t):
            verbose = int(dirs.pop(1))
        else:
            break
        dirs = dirs[1:]
    else:
        dirs = ['.']

     # insert parent directory such that
     # the code modules can be imported
    t = os.path.split(sys.path[0])
    if t:
       sys.path.insert(1, t[0])

     # print some details
    if verbose > 2:
        t = '\n           '
        print('Python %s' % sys.version.replace('\n', t))
        print("%s-bit architecture" % (8*len(struct.pack('P', 0))))
        print('')
        if verbose > 4:
            print('Sys.path:  %s\n' % t.join(sys.path))
        if verbose > 3:
            print('Test dirs: %r\n' % dirs)

     # build and run single test suite
    tst = suite(dirs, clean, verbose)
    res = unittest.TextTestRunner(verbosity=verbose).run(tst)
    if not res.wasSuccessful():
        sys.exit(1)
