#! /usr/bin/env python

import os
import sys
import unittest

from glob import glob

testfile_pattern = 'test_*.py'

def get_tests(dir='.'):
    '''Get a list of module names of all tests included in dir.'''
    res = []
     # walk recursively through all subdirectories
    if not dir.endswith('.py'):
        for sub in os.listdir(dir):
            path = dir + os.sep + sub
            if os.path.isdir(path):
                if dir == '.':
                    res.extend(get_tests(sub))
                else:
                    res.extend(get_tests(path))
     # attach module names of all tests
    for moduleName in glob(dir + os.sep + testfile_pattern):
        if dir == '.':
            moduleName = os.path.basename(moduleName)
        else:
            moduleName = dir + '.' + os.path.basename(moduleName)
        moduleName = moduleName.replace('.py', '')
        res.append(moduleName.replace(os.sep, '.'))
    return res  # sorted(res)

def suite(dirs=['.'], verbosity=2):
    '''Create a suite with all tests included in the directory of this script.

    This will also include tests from subdirectories.

    '''
    res = unittest.TestSuite()
    for dir in dirs:
        for test_module in get_tests(dir):
            components = test_module.split('.')
            module = components[-1]
            try:
                if len(components) == 1:
                    testModule = __import__(test_module)
                else:
                    testModule = __import__(test_module, globals(), locals(), [module])
                res.addTest(unittest.defaultTestLoader.loadTestsFromModule(testModule))
            except (SyntaxError, NameError, ImportError):
                print ("WARNING: Ignoring '%s' due to an error while importing!" % test_module)
                if verbosity > 2:
                    raise  # show the error
    return res
    
if __name__ == '__main__':

    verbose, dirs = 2, sys.argv[1:]
    if dirs and '-verbose'.startswith(dirs[0]):
        verbose = int(dirs[1])
        dirs = dirs[2:]

    dirs = dirs or ['.']
    if verbose > 3:
        print('dirs: %r' % dirs)

     # insert parent directory such that
     # the code modules can be imported
    sys.path.insert(0, os.path.split(sys.path[0])[0])
    if verbose > 4:
        print('sys.path: %r ...' % sys.path[:4])

    unittest.TextTestRunner(verbosity=verbose).run(suite(dirs, verbose))
