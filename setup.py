"""Setup script for Pympler.

To build, install and test Pympler and to try Pympler
before building and installing it.

The HTML documention is in the doc/ directory.  Point
your browser to the ./doc/html/index.html file.

"""
from distutils.core   import setup
from distutils.errors import DistutilsExecError
from distutils.spawn  import spawn  # raises DistutilsExecError

import pympler.metadata as metadata
import os, sys

def run_setup(include_tests=0):
    tests = []
    if include_tests:
        tests = ['test', 'test.asizeof', 'test.heapmonitor', 'test.muppy']

    setup(name=metadata.project_name,
          description=metadata.description,
          long_description = metadata.long_description,

          author=metadata.author,
          author_email=metadata.author_email,
          url=metadata.url,
          version=metadata.version,

          packages=['pympler',
                    'pympler.asizeof', 'pympler.heapmonitor',
                    'pympler.muppy'] + tests,
          
          license=metadata.license,
          platforms = ['any'],
          classifiers=['Development Status :: 3 - Alpha',
                       'Environment :: Console',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: Apache Software License',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python',
                       'Topic :: Software Development :: Bug Tracking',
                       ],
          )

_test = {'try':  '-pre-install',
         'test': '-post-install'}

if len(sys.argv) > 1 and sys.argv[1] in _test:
     # invoke  ./test/runtest.py -[pre|post]-install ...
     # to run the unittests before or after installation
    args = [sys.executable,  # this Python binary
            os.path.join('test', 'runtest.py'),
           _test[sys.argv[1]]]
    args.extend(sys.argv[2:])
    try:
        sys.exit(spawn(args))
    except DistutilsExecError:
        print("\nError: test failed or did not run.  Try '... %s -verbose 3'" % ' '.join(sys.argv))
        sys.exit(1)
else:
    # Only include tests if creating a distribution package 
    # (i.e. do not install the tests).
    run_setup('sdist' in sys.argv)
