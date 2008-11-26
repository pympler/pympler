"""Setup script for Pympler.

To build, install and test Pympler and to try Pympler
before building and installing it.

The HTML documention is in the doc/ directory.  Point
your browser to the ./doc/html/index.html file.

"""
from distutils.core   import Command
from distutils.core   import setup
from distutils.dist   import Distribution
from distutils.errors import DistutilsExecError
from distutils.spawn  import spawn  # raises DistutilsExecError
import os, sys

import pympler.metadata as metadata

class BaseTestCommand(Command):
    """Base class for the pre and the post installation commands. """
    user_options = []
    
    def initialize_options(self):
        self.param = None

    def finalize_options(self): pass

    def run(self):
        args = [sys.executable,  # this Python binary
                os.path.join('test', 'runtest.py'),
                self.param, '-verbose', '3']
        args.extend(sys.argv[2:])
        try:
            sys.exit(spawn(args))
        except DistutilsExecError:
            sys.exit(1)

class PreinstallTestCommand(BaseTestCommand):
    description = "run pre-installation tests"
    def initialize_options(self): self.param = '-pre-install'

class PostinstallTestCommand(BaseTestCommand):
    description = "run post-installation tests"
    def initialize_options(self): self.param = '-post-install'

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
          cmdclass={'try': PreinstallTestCommand,
                    'test': PostinstallTestCommand}
          )

# hack Pympler commands into setup.py help output
Distribution.common_usage += """
Pympler commands
  setup.py try     try Pympler before installation
  setup.py test    test Pympler after installation
"""

# Only include tests if creating a distribution package 
# (i.e. do not install the tests).
run_setup('sdist' in sys.argv)

