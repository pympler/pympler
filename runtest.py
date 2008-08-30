import os
import sys
import subprocess
from optparse import OptionParser


def get_tests(dir = 'test'):
    '''
    Get all tests in directory `dir`; that are files that match the pattern
    "test_*.py". A sorted list with the filenames is returned.
    '''
    tests = []

    if os.path.isfile(dir):
        if dir.startswith('test_') and dir.endswith('.py'):
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
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-P", "--python", type="string", 
                      dest="python", default="python")

    (options, args) = parser.parse_args()

    tests = []
    if not args: 
        tests = get_tests()
    else:
        for dir in args:
            tests.extend(get_tests(dir))
    tests = remove_duplicates(tests)
    tests.sort()

    os.environ['PYTHONPATH'] = os.getcwd()
    for t in tests:
        subprocess.call([options.python, t])

if __name__ == '__main__':
    main()
