"""Setup script for Pympler.

To build, install and test Pympler and to try Pympler
before building and installing it.

The HTML documention is in the doc/ directory.  Point
your browser to the ./doc/html/index.html file.

"""
import sys
import pympler.metadata as metadata
import fileinput

def _not_supported(why):
    print('NotImplementedError: ' + why + '.')
    if 'try' in sys.argv:
        print(metadata.long_description)
    sys.exit(1)

if sys.hexversion < 0x2040000:
    _not_supported('Pympler requires Python 2.4 or newer')

import os
from distutils.command.build_py import build_py
from distutils.command.install_lib import install_lib
from distutils.core   import Command
from distutils.core   import setup
from distutils.dist   import Distribution
from distutils.errors import DistutilsExecError
from distutils.spawn  import spawn  # raises DistutilsExecError

from glob import glob
from shutil import rmtree


# Hack to fix data install path: Data just points to $prefix by default.
# TODO: test on different platforms and python versions
from distutils.command.install import INSTALL_SCHEMES
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = os.path.join(scheme['data'], 'share', 'pympler')


# Write installation paths into pympler/__init__.py. Otherwise it is hardly
# possible to retrieve the installed data files reliably.
# http://www.mail-archive.com/distutils-sig@python.org/msg08883.html
class BuildPyModule(build_py):
    def build_module(self, module, module_file, package):
        cobj = self.distribution.command_obj.get('install')
        if cobj and package == 'pympler' and module == '__init__':
            # If installed from an egg with easy_install, the data will reside
            # in the egg along with the code.
            data_path = cobj.install_data
            for line in fileinput.FileInput(module_file, inplace=True):
                if line.startswith("DATA_PATH = "):
                    line = "DATA_PATH = '%s'" % data_path
                sys.stdout.write(line)
        # TODO: Cannot build bottle2 at Python3 and vice versa.
        if sys.hexversion >= 0x3000000 and module == 'bottle2':
            return
        elif sys.hexversion < 0x3000000 and module == 'bottle3':
            return
        build_py.build_module(self, module, module_file, package)


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
        tests = ['test', 'test.asizeof', 'test.tracker', 'test.muppy',
                 'test.gui']

    setup(name=metadata.project_name,
          description=metadata.description,
          long_description = metadata.long_description,

          author=metadata.author,
          author_email=metadata.author_email,
          url=metadata.url,
          version=metadata.version,

          packages=['pympler', 'pympler.util'] + tests,

          data_files=[('templates', glob('templates/*.tpl') + \
                                    glob('templates/*.js') + \
                                    glob('templates/*.css'))],

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
                    'test': PostinstallTestCommand,
                    'build_py': BuildPyModule,
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

