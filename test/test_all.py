import os
import sys
import unittest

from glob import glob

testfile_pattern = 'test_*.py'
module_list = ''

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


def get_tests_from_file(fname):
    tests = []
    f = open(fname)
    try:
        for test in f.readlines():
            tests.append(test.strip())            
    finally:
        f.close()
    return tests


def suite():
    '''Create a suite with all tests included in the directory of this script.

    This will also include tests from subdirectories.

    '''
    res = unittest.TestSuite()
    test_modules = get_tests_from_file(module_list)
    for test_module in test_modules:
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
            #print (exc)
    return res
    
if __name__ == '__main__':
    module_list = sys.argv[1]
    unittest.TextTestRunner(verbosity=2).run(suite())
