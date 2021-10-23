
import os
import re
import sys
import unittest

from io import StringIO, BytesIO
from shutil import rmtree
from tempfile import mkdtemp, mkstemp

from pympler.classtracker import ClassTracker
from pympler.classtracker_stats import ConsoleStats, HtmlStats, Stats
from pympler.asizeof import Asizer, asizeof


class Foo:
    def __init__(self):
        self.foo = 'Foo'

    def __repr__(self):
        return '<%s>' % self.foo

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
        self.out = StringIO()
        self.tracker = ClassTracker(stream=self.out)


    @property
    def output(self):
        """Return output recorded in `ClassTracker` output stream."""
        return self.out.getvalue()


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
        Stats(tracker=self.tracker).dump_stats(tmp, close=False)

        self.tracker.clear()

        stats = ConsoleStats(stream=f2)
        self.assertEqual(stats.index, {})
        self.assertEqual(stats.snapshots, [])
        tmp.seek(0)
        stats.load_stats(tmp)
        tmp.close()
        self.assertTrue('Foo' in stats.index)

        stats.print_stats()

        self.assertEqual(f1.getvalue(), f2.getvalue())

        # Test partial printing
        stats.stream = f3 = StringIO()
        stats.sort_stats()
        tolen = len(stats.sorted)
        stats.print_stats(clsname='Bar')
        self.assertEqual(len(stats.sorted), tolen)
        stats.print_summary()
        clsname = f3.getvalue().split('\n')[0]
        self.assertNotEqual(re.search('Bar', clsname), None, clsname)

        f1.close()
        f2.close()
        f3.close()


    def test_sort_stats(self):
        """Test sort_stats and reverse_order.
        """
        self.tracker.track_class(Bar, name='Bar')
        foo = Foo()
        foo.data = list(range(1000))
        bar1 = Bar()
        bar2 = Bar()
        self.tracker.track_object(foo, resolution_level=4)
        self.tracker.create_snapshot()

        stats = self.tracker.stats

        # Test sort_stats and reverse_order
        self.assertEqual(stats.sort_stats('size'), stats)
        self.assertEqual(stats.sorted[0].classname, 'Foo')
        stats.reverse_order()
        self.assertEqual(stats.sorted[0].classname, 'Bar')
        stats.sort_stats('classname', 'birth')
        self.assertEqual(stats.sorted[0].classname, 'Bar')
        self.assertRaises(ValueError, stats.sort_stats, 'name', 42, 'classn')
        stats.sort_stats('classname')


    def test_dump_load_with_filename(self):
        """Test serialization with filename.
        """
        foo = Foo()
        self.tracker.track_object(foo, resolution_level=2)
        self.tracker.create_snapshot()
        fhandle, fname = mkstemp(prefix='pympler_test_dump')
        os.close(fhandle)
        try:
            self.tracker.stats.dump_stats(fname)
            output = StringIO()
            stats = ConsoleStats(filename=fname, stream=output)
            stats.print_stats()
            self.assertTrue('<Foo>' in output.getvalue(), output.getvalue())
            # Check if a Stats loaded from a dump can be dumped again
            stats.dump_stats(fname)
        finally:
            os.unlink(fname)


    def test_tracked_classes(self):
        """Test listing tracked classes.
        """
        self.tracker.track_class(Foo, name='Foo')
        self.tracker.track_class(Bar, name='Bar')

        foo = Foo()
        self.tracker.create_snapshot()
        bar = Bar()
        self.tracker.create_snapshot()
        foo = FooNew()
        self.tracker.track_object(foo)
        self.tracker.create_snapshot()

        stats = self.tracker.stats
        self.assertEqual(stats.tracked_classes, ['Bar', 'Foo', 'FooNew'])
        stats.print_summary()


    def test_print_stats(self):
        """Test printing class-filtered statistics.
        """
        self.tracker.track_class(Foo, name='Foo', trace=True)
        self.tracker.track_class(Bar, name='Bar')

        foo = Foo()
        bar = Bar()

        self.tracker.create_snapshot()

        stats = self.tracker.stats
        stats.print_stats(clsname='Foo')
        self.assertTrue('Foo' in self.output, self.output)
        self.assertFalse('Bar' in self.output, self.output)
        self.assertTrue('foo = Foo()' in self.output, self.output)


    def test_print_stats_limit(self):
        """Test printing limited statistics.
        """
        self.tracker.track_class(Foo, name='Foo')

        foo = [Foo() for _ in range(10)]

        self.tracker.create_snapshot()

        stats = self.tracker.stats
        stats.print_stats(limit=3)
        self.assertEqual(self.output.count('<Foo>'), 3)

        self.out.seek(0)
        self.out.truncate()

        stats.print_stats(limit=0.5)
        self.assertEqual(self.output.count('<Foo>'), 5)


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

        stats = self.tracker.stats
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

        stats = self.tracker.stats
        for fp in stats.snapshots:
            if fp.desc == 'Merge test':
                stats.annotate_snapshot(fp)
                self.assertTrue(hasattr(fp, 'classes'))
                classes = fp.classes
                stats.annotate_snapshot(fp)
                self.assertEqual(fp.classes, classes)
                self.assertTrue('Foo' in fp.classes, fp.classes)
                self.assertTrue('merged' in fp.classes['Foo'])
                fm = fp.classes['Foo']['merged']
                self.assertEqual(fm.size, sz1.size + sz2.size, (fm.size, str(sz1), str(sz2)))
                refs = {}
                for ref in fm.refs:
                    refs[ref.name] = ref
                self.assertTrue('__dict__' in refs.keys(), refs.keys())
                refs2 = {}
                for ref in refs['__dict__'].refs:
                    refs2[ref.name] = ref
                self.assertTrue('[V] a' in refs2.keys(), refs2.keys())
                self.assertTrue('[V] b' in refs2.keys(), refs2.keys())
                self.assertEqual(refs2['[V] a'].size, asizeof(f1.a, f2.a))


    def test_html(self):
        """Test emitting HTML statistics."""
        self.tracker.track_class(Foo, name='Foo', resolution_level=2)
        self.tracker.track_class(Bar, name='Bar', trace=True)

        f1 = Foo()
        f1.a = list(range(100000))
        f2 = Foo()
        f2.a = list(range(1000))
        f2.b = 'This is some stupid spam.'
        f1 = Bar()

        self.tracker.create_snapshot('Merge test')

        stats = HtmlStats(tracker=self.tracker)
        try:
            target = mkdtemp(prefix='pympler_test')
            output = os.path.join(target, 'footest.html')
            stats.create_html(output)

            source = open(output).read()
            # Ensure relative links are used
            fname = os.path.join('footest_files', 'Foo.html')
            self.assertTrue('<a href="%s">' % fname in source, (fname, source))
        finally:
            rmtree(target)


    def test_charts(self):
        """Test emitting graphic charts."""
        self.tracker.track_class(Foo, name='Foo', resolution_level=2)

        f1 = Foo()
        f1.a = list(range(1000))
        f2 = Foo()
        f2.a = list(range(100))
        f2.b = 'This is some stupid spam.'

        self.tracker.create_snapshot('Merge test')

        from pympler import charts
        try:
            target = mkdtemp(prefix='pympler_test')
            output = os.path.join(target, 'timespace.png')
            charts.tracker_timespace(output, self.tracker.stats)
        finally:
            rmtree(target)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [ LogTestCase ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
