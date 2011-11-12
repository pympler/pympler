import os

DATA_PATH = ''

# DATA_PATH will be initialized from distutils when installing. If Pympler is
# installed via setuptools/easy_install, the data will be installed alongside
# the source files instead.
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
