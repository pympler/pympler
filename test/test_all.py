import inspect
import os
import sys
import unittest

from glob import glob
from unittest import defaultTestLoader

testfile_pattern = 'test_*.py'
# location of this very module
_modulepath = os.path.abspath(os.path.dirname(inspect.getfile(lambda foo:foo)))

def get_tests(dir='.'):
    '''Get a list of module names of all tests included in dir.'''
    res = []
    # walk recursively through all subdirectories
    entries = os.listdir(dir)
    for entry in entries:
        if os.path.isdir(dir + os.sep + entry):
            if dir == '.':
                res.extend(get_tests(entry))
            else:
                res.extend(get_tests(dir + os.sep + entry))
    # attach module names of all tests
    for moduleName in glob(dir + os.sep + testfile_pattern):
        if dir == '.':
            moduleName = os.path.basename(moduleName)
        else:
            moduleName = dir + '.' + os.path.basename(moduleName)
        moduleName = moduleName.replace('.py', '')
        res.append(moduleName)
    return res

def suite():
    '''Create a suite with all tests included in the directory of this script.

    This will also include tests from subdirectories.

    '''
    res = unittest.TestSuite()
    test_modules = get_tests()
    for test_module in test_modules:
        package, sep, module = test_module.rpartition('.')
        if package == '':
            testModule = __import__(test_module)
        else:
            testModule = __import__(test_module, fromlist=module)
        res.addTest(defaultTestLoader.loadTestsFromModule(testModule))
    return res
    
if __name__ == '__main__':
    sys.path.append(_modulepath + os.sep + "..")
    unittest.TextTestRunner(verbosity=2).run(suite())
