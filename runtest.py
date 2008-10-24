#!/usr/bin/env python

import os
import sys
import subprocess
from tempfile import mkstemp
from optparse import OptionParser


def get_tests(dir = 'test'):
    '''
    Get all tests in directory `dir`; that are files that match the pattern
    "test_*.py". A sorted list with the filenames is returned.
    '''
    tests = []

    if os.path.isfile(dir):
        fn = os.path.basename(dir)
        if fn.startswith('test_') and fn.endswith('.py'):
            tests.append(dir)

    elif os.path.isdir(dir):
        for root, dirs, files in os.walk(dir):
            for fn in files:
                if fn.startswith('test_') and fn.endswith('.py'):
                    tests.append(os.path.join(root,fn))

    return tests


def remove_duplicates(list):
    d = {}.fromkeys(list)
    return d.keys()


def main():
    '''
    Find and run all specified tests.
    '''
    usage = "usage: %prog [options] tests"
    parser = OptionParser(usage)
    parser.add_option("-P", "--python", type="string", 
                      dest="python", default="python")

    (options, args) = parser.parse_args()

    project_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    test_path = os.path.join(project_path, 'test')

    tests = []
    if not args:
        args = [test_path]
    for dir in args:
        tests.extend(get_tests(dir))
    tests = remove_duplicates(tests)
    tests.sort()
    (fd, test_list) = mkstemp(suffix='.txt')
    f = os.fdopen(fd, 'w')
    for t in tests:
        t = t.replace(project_path, '')
        t = os.path.splitext(t)[0].replace(os.sep, '.')
        if t[0] == '.': 
            t = t[1:]
        if not t == 'test.test_all':
            f.write(t+'\n')
    f.close()

    os.environ['PYTHONPATH'] = project_path
    subprocess.call([options.python, 
                     os.path.join(test_path, 'test_all.py'),
                     test_list])
    os.remove(test_list)

if __name__ == '__main__':
    main()
