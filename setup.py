"""Setup script for Pympler.

To build, install and test Pympler and to try Pympler
before building and installing it.

The HTML documentation is in the doc/ directory.  Point
your browser to the ./doc/html/index.html file.

"""
import sys
import pympler.metadata as metadata


def _not_supported(why):
    print('NotImplementedError: ' + why + '.')
    if 'try' in sys.argv:
        print(metadata.long_description)
    sys.exit(1)


if sys.hexversion < 0x2070000:
    _not_supported('Pympler requires Python 2.7 or newer')

import os
from distutils.command.install_lib import install_lib
from distutils.core import Command
from distutils.core import setup
from distutils.dist import Distribution
from distutils.errors import DistutilsExecError
from distutils.spawn import spawn  # raises DistutilsExecError

from shutil import rmtree


# Remove all already installed modules. Make sure old removed or renamed
# modules cannot be imported anymore.
class InstallCommand(install_lib):
    def run(self):
        target_path = os.path.join(self.install_dir, 'pympler')
        try:
            rmtree(target_path)
            print ("purging %s" % target_path)
        except OSError:
            pass
        install_lib.run(self)


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
        try:
            sys.exit(spawn(args))
        except DistutilsExecError:
            sys.exit(1)


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

    setup(name=metadata.project_name,
          description=metadata.description,
          long_description=metadata.long_description,

          author=metadata.author,
          author_email=metadata.author_email,
          url=metadata.url,
          version=metadata.version,

          packages=['pympler', 'pympler.util'] + tests,

          package_data={'pympler': ['templates/*.html',
                                    'templates/*.tpl',
                                    'templates/*.js',
                                    'templates/*.css',
                                    'static/*.js']},

          license=metadata.license,
          platforms=['any'],
          classifiers=['Development Status :: 4 - Beta',
                       'Environment :: Console',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: Apache Software License',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python',
                       'Programming Language :: Python :: 2',
                       'Programming Language :: Python :: 2.7',
                       'Programming Language :: Python :: 3',
                       'Programming Language :: Python :: 3.3',
                       'Programming Language :: Python :: 3.4',
                       'Programming Language :: Python :: 3.5',
                       'Programming Language :: Python :: 3.6',
                       'Programming Language :: Python :: 3.7',
                       'Topic :: Software Development :: Bug Tracking',
                       ],
          cmdclass={'try': PreinstallTestCommand,
                    'test': PostinstallTestCommand,
                    'install_lib': InstallCommand,
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
