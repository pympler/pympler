"""
This example shows how to track classes and display statistics at the end of
the script using the web GUI. Snapshots are taken manually. This setup makes
sense with simple batch processing jobs where you want to track memory usage at
certain points in time.
"""

from random import randint

from pympler import web
from pympler.classtracker import ClassTracker


class Alpha(object):
    def __init__(self):
        self.data = 100 * '0xdeadbeef'


class Beta(object):
    def __init__(self):
        self.data = randint(200,300) * '0xdeadbeef'


class Gamma(object):
    def __init__(self):
        self.mutable = list(range(10))
        self.immutable = tuple(range(10))


def create_data(tracker, iterations=20, obj_per_iteration=100):
    objects = []
    for x in range(iterations):
        for y in range(obj_per_iteration):
            objects.append(Alpha())
            objects.append(Beta())
        objects.append(Gamma())
        tracker.create_snapshot()

    return objects


tracker = ClassTracker()

tracker.track_class(Alpha)
tracker.track_class(Beta)
tracker.track_class(Gamma, trace=True, resolution_level=2)

print ("Create data")
tracker.create_snapshot()
data = create_data(tracker)
print ("Drop data")
del data
tracker.create_snapshot()

web.start_profiler(debug=True, stats=tracker.stats)
