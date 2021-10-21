"""Setup script for Pympler.

To build, install and test Pympler and to try Pympler
before building and installing it.

The HTML documentation is in the doc/ directory.  Point
your browser to the ./doc/html/index.html file.

"""
import sys


def _not_supported(why):
    print('NotImplementedError: ' + why + '.')
    sys.exit(1)


if sys.hexversion < 0x3050000:
    _not_supported('Pympler requires Python 3.5 or newer')

import os
from setuptools import Command
from setuptools import setup
from setuptools import Distribution
from subprocess import run


class BaseTestCommand(Command):
    """Base class for the pre and the post installation commands. """
    user_options = []

    def initialize_options(self):
        self.param = None

    def finalize_options(self):
        pass

    def run(self):
        args = [sys.executable,  # this Python binary
                os.path.join('test', 'runtest.py'),
                self.param, '-verbose', '3']
        args.extend(sys.argv[2:])
        sys.exit(run(args).returncode)


class PreinstallTestCommand(BaseTestCommand):
    description = "run pre-installation tests"

    def initialize_options(self):
        self.param = '-pre-install'


class PostinstallTestCommand(BaseTestCommand):
    description = "run post-installation tests"

    def initialize_options(self):
        self.param = '-post-install'


def run_setup(include_tests=0):
    tests = []
    if include_tests:
        tests = ['test', 'test.asizeof', 'test.tracker', 'test.muppy',
                 'test.gui']

    setup(packages=['pympler', 'pympler.util'] + tests,
          package_data={'pympler': ['templates/*.html',
                                    'templates/*.tpl',
                                    'templates/*.js',
                                    'templates/*.css',
                                    'static/*.js']},
          platforms=['any'],
          classifiers=['Development Status :: 4 - Beta',
                       'Environment :: Console',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: Apache Software License',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python',
                       'Programming Language :: Python :: 3',
                       'Programming Language :: Python :: 3.5',
                       'Programming Language :: Python :: 3.6',
                       'Programming Language :: Python :: 3.7',
                       'Programming Language :: Python :: 3.8',
                       'Programming Language :: Python :: 3.9',
                       'Programming Language :: Python :: 3.10',
                       'Topic :: Software Development :: Bug Tracking',
                       ],
          cmdclass={'try': PreinstallTestCommand,
                    'test': PostinstallTestCommand,
                    }
          )


try:  # hack Pympler commands into setup.py help output
    Distribution.common_usage += """
Pympler commands
  setup.py try     try Pympler before installation
  setup.py test    test Pympler after installation
"""
except AttributeError:
    pass

# Only include tests if creating a distribution package
# (i.e. do not install the tests).
run_setup('sdist' in sys.argv)
