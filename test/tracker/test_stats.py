import unittest
import re
from pympler.util.compat2and3 import StringIO, BytesIO

from pympler.tracker import ClassTracker
from pympler.tracker.stats import *

class Foo:
    def __init__(self):
        self.foo = 'foo'

class Bar(Foo):
    def __init__(self):
        Foo.__init__(self)
        self.bar = 'bar'

class FooNew(object):
    def __init__(self):
        self.foo = 'foo'

class BarNew(FooNew):
    def __init__(self):
        super(BarNew, self).__init__()

class LogTestCase(unittest.TestCase):

    def setUp(self):
        self.tracker = ClassTracker()

    def tearDown(self):
        self.tracker.stop_periodic_snapshots()
        self.tracker.clear()

    def test_dump(self):
        """Test serialization of log data.
        """
        foo = Foo()
        foo.data = range(1000)
        bar = Bar()

        self.tracker.track_object(foo, resolution_level=4)
        self.tracker.track_object(bar)

        self.tracker.create_snapshot('Footest')

        f1 = StringIO()
        f2 = StringIO()

        ConsoleStats(tracker=self.tracker, stream=f1).print_stats()

        tmp = BytesIO()
        Stats(tracker=self.tracker).dump_stats(tmp, close=0)

        self.tracker.clear()

        stats = ConsoleStats(stream=f2)
        assert stats.index is None
        assert stats.footprint is None
        tmp.seek(0)
        stats.load_stats(tmp)
        tmp.close()
        assert 'Foo' in stats.index

        stats.print_stats()

        assert f1.getvalue() == f2.getvalue()

        # Test sort_stats and reverse_order
        assert stats.sort_stats('size') == stats
        assert stats.sorted[0].classname == 'Foo'
        stats.reverse_order()
        assert stats.sorted[0].classname == 'Bar'
        stats.sort_stats('classname', 'birth')
        assert stats.sorted[0].classname == 'Bar'
        self.assertRaises(ValueError, stats.sort_stats, 'name', 42, 'classn')
        assert stats.diff_stats(stats) == None # Not yet implemented

        # Test partial printing
        stats.stream = f3 = StringIO()
        stats.sort_stats()
        tolen = len(stats.sorted)
        stats.print_stats(filter='Bar',limit=0.5)
        assert len(stats.sorted) == tolen
        stats.print_summary()
        clsname = f3.getvalue().split('\n')[0]
        assert re.search('\.Bar', clsname) != None, clsname
        assert len(f3.getvalue()) < len(f1.getvalue())

        f1.close()
        f2.close()
        f3.close()


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [ LogTestCase ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
