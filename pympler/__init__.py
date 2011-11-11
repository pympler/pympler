import os

DATA_PATH = '/home/lha/.virtualenvs/pympler_egg/share/pympler'
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
