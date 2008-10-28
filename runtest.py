#!/usr/bin/env python

import os
import sys
import subprocess
import re
from tempfile import mkstemp
from optparse import OptionParser

def get_files(location = 'test', pattern = '^test_[^\n]*.py$'):
    '''
    Get all files in directory `location` recursively that match the specified
    `pattern`.
    '''
    res = []
    pattern = re.compile(pattern)
    if os.path.isfile(location):
        fn = os.path.basename(location)
        if pattern.match(fn):
            res.append(location)
    elif os.path.isdir(location):
        for root, dirs, files in os.walk(location):
            for fn in files:
                if pattern.match(fn):
                    res.append(os.path.join(root,fn))
    return res

def remove_duplicates(list):
    d = {}.fromkeys(list)
    return d.keys()

def run_unittests(project_path, python_path='python', locations=[]):
    '''
    Run unittests for all modules found in the specified locations.

    If no location is given, all unittests will be executed.
    '''
    if locations == []:
        locations = ['test']
    tests = []
    for location in locations:
        tests.extend(get_files(location))
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
    subprocess.call([python_path, 
                     os.path.join('test', 'test_all.py'),
                     test_list])
    os.remove(test_list)

def run_pychecker(locations = []):
    '''
    Run pychecker against all specified source files.
    '''
    sources = []
    if locations == []:
        locations = ['pympler']
    for location in locations:
        sources.extend(get_files(location = location, pattern = '[^\n]*.py$'))
    for src in sources:
        print ("CHECKING %s" % src)
        subprocess.call(['python', 'tools/pychok.py', '-no', '--stdlib', 
                         '--quiet', src])

def test_docs(path, actions=['html', 'doctest']):
    '''Test documentation with sphinx.

    Possible entries for the actions list are all valid parameters for the
    'make' command inside the documentation directory.
    '''
    cwd = os.getcwd()
    os.chdir(path)
    for action in actions:
        subprocess.call(['make', 'clean'])
        subprocess.call(['make', action])
        subprocess.call(['make', 'clean'])
    os.chdir(cwd)

def main():
    '''
    Find and run all specified tests.
    '''
    usage = "usage: %prog [options] tests"
    parser = OptionParser(usage)
    parser.add_option("-P", "--python", type="string", 
                      dest="python", default="python")
    parser.add_option("--no-unittests", action='store_true', default=False,
                      dest="no_unittests", help="Do not run unittests.")
    parser.add_option("--html", action='store_true', default=False,
                      dest="html", help="Run creation of documentation.")
    parser.add_option("--doctest", action='store_true', default=False,
                      dest="doctest", help="Run doctests.")
    parser.add_option("--all-tests", action='store_true', default=False,
                      dest="alltests", help="Run all available tests.")
    parser.add_option("--pychecker", action="store_true", default=False,
                      dest="pychecker", help="Static analysis with PyChecker")

    (options, args) = parser.parse_args()
    project_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    test_path = os.path.join(project_path, 'test')
    doc_path = os.path.join(project_path, 'doc')

    if options.alltests:
        options.html = True
        options.doctest = True
        options.no_unittests = False
    if options.html:
        print "Create documention"
        print "=================="
        test_docs(doc_path, actions=['html'])
        print
    if options.doctest:
        print "Run doctests"
        print "============"
        test_docs(doc_path, actions=['doctest'])
        print 
    if options.pychecker:
        print "Run pychecker"
        print "============="
        run_pychecker(args)
        return
    if options.no_unittests:
        return
        
    print "Run unittests"
    print "============="
    run_unittests(project_path, options.python, args)

if __name__ == '__main__':
    main()
