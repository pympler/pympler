
import os
import re
import sys
import unittest

from pympler.util.compat import StringIO, BytesIO

from pympler.tracker import ClassTracker
from pympler.tracker.stats import *
from pympler.asizeof import Asizer, asizeof

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
        self.assert_(stats.index is None)
        self.assert_(stats.footprint is None)
        tmp.seek(0)
        stats.load_stats(tmp)
        tmp.close()
        self.assert_('Foo' in stats.index)

        stats.print_stats()

        self.assertEqual(f1.getvalue(), f2.getvalue())

        # Test sort_stats and reverse_order
        self.assertEqual(stats.sort_stats('size'), stats)
        self.assertEqual(stats.sorted[0].classname, 'Foo')
        stats.reverse_order()
        self.assertEqual(stats.sorted[0].classname, 'Bar')
        stats.sort_stats('classname', 'birth')
        self.assertEqual(stats.sorted[0].classname, 'Bar')
        self.assertRaises(ValueError, stats.sort_stats, 'name', 42, 'classn')

        # Test partial printing
        stats.stream = f3 = StringIO()
        stats.sort_stats()
        tolen = len(stats.sorted)
        stats.print_stats(clsname='Bar',limit=0.5)
        self.assertEqual(len(stats.sorted), tolen)
        stats.print_summary()
        clsname = f3.getvalue().split('\n')[0]
        self.assertNotEqual(re.search('\.Bar', clsname), None, clsname)
        self.assert_(len(f3.getvalue()) < len(f1.getvalue()))

        f1.close()
        f2.close()
        f3.close()

    def test_snapshots(self):
        """Test multiple snapshots.
        """
        self.tracker.track_class(Foo, name='Foo')
        self.tracker.track_class(Bar, name='Bar')
        self.tracker.track_class(FooNew, name='FooNew')

        self.tracker.create_snapshot()
        f1 = Foo()
        self.tracker.create_snapshot()
        f2 = Foo()
        f3 = FooNew()
        self.tracker.create_snapshot()
        b = Bar()
        del b
        self.tracker.create_snapshot()

        stream = StringIO()
        stats = ConsoleStats(tracker=self.tracker, stream=stream)
        stats.print_stats()
        stats.print_summary()

    def test_merge(self):
        """Test merging of reference trees.
        """
        self.tracker.track_class(FooNew, name='Foo', resolution_level=2)

        f1 = FooNew()
        f1.a = list(range(1000))
        f2 = FooNew()
        f2.a = list(range(100))
        f2.b = 'This is some stupid spam.'

        self.tracker.create_snapshot('Merge test')

        sizer = Asizer()
        sz1 = sizer.asized(f1)
        sz2 = sizer.asized(f2)

        stats = Stats(tracker=self.tracker)
        for fp in stats.footprint:
            if fp.desc == 'Merge test':
                stats.annotate_snapshot(fp)
                self.assert_(hasattr(fp, 'classes'))
                self.assert_('Foo' in fp.classes, fp.classes)
                self.assert_('merged' in fp.classes['Foo'])
                fm = fp.classes['Foo']['merged']
                self.assertEqual(fm.size, sz1.size + sz2.size, (fm.size, str(sz1), str(sz2)))
                refs = {}
                for ref in fm.refs:
                    refs[ref.name] = ref
                self.assert_('__dict__' in refs.keys(), refs.keys())
                refs2 = {}
                for ref in refs['__dict__'].refs:
                    refs2[ref.name] = ref
                self.assert_('[V] a' in refs2.keys(), refs2.keys())
                self.assert_('[V] b' in refs2.keys(), refs2.keys())
                self.assertEqual(refs2['[V] a'].size, asizeof(f1.a, f2.a))

    def test_html(self):
        """Test emitting HTML statistics."""
        self.tracker.track_class(Foo, name='Foo', resolution_level=2)

        f1 = Foo()
        f1.a = list(range(100000))
        f2 = Foo()
        f2.a = list(range(1000))
        f2.b = 'This is some stupid spam.'

        self.tracker.create_snapshot('Merge test')

        stats = HtmlStats(tracker=self.tracker)
        output = 'tmp/data/footest.html'
        stats.create_html(output)

        source = open(output).read()
        # Ensure relative links are used
        fname = os.path.join('footest_files', 'Foo.html')
        self.assert_('<a href="%s">' % fname in source, (fname, source))


    def test_charts(self):
        """Test emitting graphic charts."""
        self.tracker.track_class(Foo, name='Foo', resolution_level=2)

        f1 = Foo()
        f1.a = list(range(1000))
        f2 = Foo()
        f2.a = list(range(100))
        f2.b = 'This is some stupid spam.'

        self.tracker.create_snapshot('Merge test')

        stats = Stats(tracker=self.tracker)
        from pympler.gui import charts
        charts.tracker_timespace('tmp/data/timespace.png', stats)

if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [ LogTestCase ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
