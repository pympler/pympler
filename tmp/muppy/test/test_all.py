import inspect
import os
import sys
import unittest

from glob import glob
from unittest import defaultTestLoader

def suite():
    mod_path = os.path.dirname(inspect.getfile(lambda foo:foo))
    sys.path.append(mod_path + os.sep + "..")
    s = unittest.TestSuite()
    for moduleName in glob(mod_path + os.sep + "test_*.py"):
        moduleName = os.path.basename(moduleName)
        moduleName = moduleName.replace('.py', '')
        if moduleName != 'test_all':
            testModule = __import__(moduleName)
            s.addTest(defaultTestLoader.loadTestsFromModule(testModule))
    return s
    
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

