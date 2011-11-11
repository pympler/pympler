import os

DATA_PATH = ''
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
