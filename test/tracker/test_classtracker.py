import sys
import time
import unittest

from pympler.classtracker import ClassTracker
import pympler.process


class Empty:
    pass

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


class TrackObjectTestCase(unittest.TestCase):

    def setUp(self):
        self.tracker = ClassTracker()

    def tearDown(self):
        self.tracker.detach_all()

    def test_track_object(self):
        """Test object registration.
        """
        foo = Foo()
        bar = Bar()

        self.tracker.track_object(foo)
        self.tracker.track_object(bar)

        self.assertTrue(id(foo) in self.tracker.objects)
        self.assertTrue(id(bar) in self.tracker.objects)

        self.assertTrue('Foo' in self.tracker.index)
        self.assertTrue('Bar' in self.tracker.index)

        self.assertEqual(self.tracker.objects[id(foo)].ref(),foo)
        self.assertEqual(self.tracker.objects[id(bar)].ref(),bar)

    def test_type_errors(self):
        """Test intrackable objects.
        """
        i = 42
        j = 'Foobar'
        k = [i,j]
        l = {i: j}

        self.assertRaises(TypeError, self.tracker.track_object, i)
        self.assertRaises(TypeError, self.tracker.track_object, j)
        self.assertRaises(TypeError, self.tracker.track_object, k)
        self.assertRaises(TypeError, self.tracker.track_object, l)

        self.assertTrue(id(i) not in self.tracker.objects)
        self.assertTrue(id(j) not in self.tracker.objects)
        self.assertTrue(id(k) not in self.tracker.objects)
        self.assertTrue(id(l) not in self.tracker.objects)

    def test_track_by_name(self):
        """Test registering objects by name.
        """
        foo = Foo()

        self.tracker.track_object(foo, name='Foobar')

        self.assertTrue('Foobar' in self.tracker.index        )
        self.assertEqual(self.tracker.index['Foobar'][0].ref(),foo)

    def test_keep(self):
        """Test lifetime of tracked objects.
        """
        foo = Foo()
        bar = Bar()

        self.tracker.track_object(foo, keep=1)
        self.tracker.track_object(bar)

        idfoo = id(foo)
        idbar = id(bar)

        del foo
        del bar

        self.assertTrue(self.tracker.objects[idfoo].ref() is not None)
        self.assertTrue(self.tracker.objects[idbar].ref() is None)

    def test_mixed_tracking(self):
        """Test mixed instance and class tracking.
        """
        foo = Foo()
        self.tracker.track_object(foo)
        self.tracker.create_snapshot()
        self.tracker.track_class(Foo)
        objs = []
        for _ in range(10):
            objs.append(Foo())
        self.tracker.create_snapshot()

    def test_recurse(self):
        """Test recursive sizing and saving of referents.
        """
        foo = Foo()

        self.tracker.track_object(foo, resolution_level=1)
        self.tracker.create_snapshot()

        fp = self.tracker.objects[id(foo)].snapshots[-1]
        refs = fp[1].refs
        dref = [r for r in refs if r.name == '__dict__']
        self.assertEqual(len(dref),1)
        dref = dref[0]
        self.assertTrue(dref.size > 0, dref.size)
        self.assertTrue(dref.flat > 0, dref.flat)
        self.assertEqual(dref.refs,())

        # Test track_change and more fine-grained resolution
        self.tracker.track_change(foo, resolution_level=2)
        self.tracker.create_snapshot()

        fp = self.tracker.objects[id(foo)].snapshots[-1]
        refs = fp[1].refs
        dref = [r for r in refs if r.name == '__dict__']
        self.assertEqual(len(dref),1)
        dref = dref[0]
        namerefs = [r.name for r in dref.refs]
        self.assertTrue('[K] foo' in namerefs, namerefs)
        self.assertTrue("[V] foo: 'foo'" in namerefs, namerefs)


class SnapshotTestCase(unittest.TestCase):

    def setUp(self):
        self.tracker = ClassTracker()

    def tearDown(self):
        self.tracker.stop_periodic_snapshots()
        self.tracker.clear()

    def test_timestamp(self):
        """Test timestamp of snapshots.
        """
        foo = Foo()
        bar = Bar()

        self.tracker.track_object(foo)
        self.tracker.track_object(bar)

        self.tracker.create_snapshot()
        self.tracker.create_snapshot()
        self.tracker.create_snapshot()

        refts = [fp.timestamp for fp in self.tracker.snapshots]
        for to in self.tracker.objects.values():
            ts = [t for (t,sz) in to.snapshots[1:]]
            self.assertEqual(ts,refts)

    def test_snapshot_members(self):
        """Test existence and value of snapshot members.
        """
        foo = Foo()
        self.tracker.track_object(foo)
        self.tracker.create_snapshot()
        self.tracker.create_snapshot(compute_total=True)

        fp = self.tracker.snapshots[0]
        fp_with_total = self.tracker.snapshots[1]

        self.assertTrue(fp.overhead > 0, fp.overhead)
        self.assertTrue(fp.tracked_total > 0, fp.tracked_total)
        self.assertEqual(fp.asizeof_total, 0)

        self.assertTrue(fp_with_total.asizeof_total > 0, fp_with_total.asizeof_total)
        self.assertTrue(fp_with_total.asizeof_total >= fp_with_total.tracked_total)

        if pympler.process.is_available():
            procmem = fp.system_total
            self.assertEqual(fp.total, procmem.vsz)
            self.assertTrue(procmem.vsz > 0, procmem)
            self.assertTrue(procmem.rss > 0, procmem)
            self.assertTrue(procmem.vsz >= procmem.rss, procmem)
            self.assertTrue(procmem.vsz > fp.overhead, procmem)
            self.assertTrue(procmem.vsz > fp.tracked_total, procmem)
            self.assertTrue(fp_with_total.system_total.vsz > fp_with_total.asizeof_total)
        else:
            self.assertEqual(fp_with_total.total, fp_with_total.asizeof_total)
            self.assertEqual(fp.total, fp.tracked_total)


    def test_desc(self):
        """Test snapshot label.
        """
        self.tracker.create_snapshot()
        self.tracker.create_snapshot('alpha')
        self.tracker.create_snapshot(description='beta')
        self.tracker.create_snapshot(42)

        self.assertEqual(len(self.tracker.snapshots), 4)
        self.assertEqual(self.tracker.snapshots[0].desc, '')
        self.assertEqual(self.tracker.snapshots[1].desc, 'alpha')
        self.assertEqual(self.tracker.snapshots[2].desc, 'beta')
        self.assertEqual(self.tracker.snapshots[3].desc, '42')

        snapshot = self.tracker.snapshots[0]
        self.assertEqual(snapshot.label, '%.3fs' % snapshot.timestamp)
        snapshot = self.tracker.snapshots[1]
        self.assertEqual(snapshot.label, 'alpha (%.3fs)' % snapshot.timestamp)
        snapshot = self.tracker.snapshots[3]
        self.assertEqual(snapshot.label, '42 (%.3fs)' % snapshot.timestamp)


    def test_background_monitoring(self):
        """Test background monitoring.
        """
        self.tracker.start_periodic_snapshots(0.1)
        self.assertEqual(self.tracker._periodic_thread.interval, 0.1)
        self.assertEqual(self.tracker._periodic_thread.getName(), 'BackgroundMonitor')
        for x in range(10): # try to interfere
            self.tracker.create_snapshot(str(x))
        time.sleep(0.5)
        self.tracker.start_periodic_snapshots(0.2)
        self.assertEqual(self.tracker._periodic_thread.interval, 0.2)
        self.tracker.stop_periodic_snapshots()
        self.assertTrue(self.tracker._periodic_thread is None)
        self.assertTrue(len(self.tracker.snapshots) > 10)


class TrackClassTestCase(unittest.TestCase):

    def setUp(self):
        self.tracker = ClassTracker()

    def tearDown(self):
        self.tracker.stop_periodic_snapshots()
        self.tracker.clear()

    def test_type_errors(self):
        """Test invalid parameters for class tracking.
        """
        i = 42
        j = 'Foobar'
        k = [i,j]
        l = {i: j}
        foo = Foo()
        bar = Bar()

        self.assertRaises(TypeError, self.tracker.track_class, i)
        self.assertRaises(TypeError, self.tracker.track_class, j)
        self.assertRaises(TypeError, self.tracker.track_class, k)
        self.assertRaises(TypeError, self.tracker.track_class, l)
        self.assertRaises(TypeError, self.tracker.track_class, foo)
        self.assertRaises(TypeError, self.tracker.track_class, bar)

        self.assertTrue(id(i) not in self.tracker.objects)
        self.assertTrue(id(j) not in self.tracker.objects)
        self.assertTrue(id(k) not in self.tracker.objects)
        self.assertTrue(id(l) not in self.tracker.objects)

    def test_track_class(self):
        """Test tracking objects through classes.
        """
        self.tracker.track_class(Foo)
        self.tracker.track_class(Bar)
        self.tracker.track_class(Empty)
        self.tracker.track_class(Foo)

        foo = Foo()
        bar = Bar()
        empty = Empty()

        self.assertTrue(id(foo) in self.tracker.objects)
        self.assertTrue(id(bar) in self.tracker.objects)
        self.assertTrue(id(empty) in self.tracker.objects)

    def test_track_class_new(self):
        """Test tracking new style classes.
        """
        self.tracker.track_class(FooNew)
        self.tracker.track_class(BarNew)

        foo = FooNew()
        bar = BarNew()

        self.assertTrue(id(foo) in self.tracker.objects)
        self.assertTrue(id(bar) in self.tracker.objects)

    def test_track_by_name(self):
        """Test registering objects by name.
        """
        self.tracker.track_class(Foo, name='Foobar')

        foo = Foo()

        self.assertTrue('Foobar' in self.tracker.index        )
        self.assertEqual(self.tracker.index['Foobar'][0].ref(),foo)

    def test_keep(self):
        """Test lifetime of tracked objects.
        """
        self.tracker.track_class(Foo, keep=1)
        self.tracker.track_class(Bar)

        foo = Foo()
        bar = Bar()

        idfoo = id(foo)
        idbar = id(bar)

        del foo
        del bar

        self.assertTrue(self.tracker.objects[idfoo].ref() is not None)
        self.assertTrue(self.tracker.objects[idbar].ref() is None)

    def test_class_history(self):
        """Test instance history of tracked class.
        """
        self.tracker.track_class(Foo, name='Foo')
        f1 = Foo()
        f2 = Foo()
        f3 = Foo()
        del f1
        del f2
        f4 = Foo()
        del f3
        del f4

        instances = [cnt for _, cnt in self.tracker.history['Foo']]
        self.assertEqual(instances, [1, 2, 3, 2, 1, 2, 1, 0])

    def test_trace(self):
        """Test instantiation tracing of tracked objects.
        """
        from inspect import stack

        self.tracker.track_class(Foo, trace=True)
        self.tracker.track_class(BarNew, trace=True)

        foo = Foo()
        bar = BarNew()

        idfoo = id(foo)
        idbar = id(bar)

        trace = []
        st = stack()
        try:
            for fr in st:
                trace.insert(0, fr[1:])
        finally:
            del st

        self.assertEqual(self.tracker.objects[idfoo].trace[-1][3][0].strip(),"foo = Foo()")
        self.assertEqual(self.tracker.objects[idfoo].trace[:-1],trace[:-1], trace)
        self.assertEqual(self.tracker.objects[idbar].trace[:-1],trace[:-1], trace)

    def test_detach(self):
        """Test detaching from tracked classes.
        """
        self.tracker.track_class(Foo)
        self.tracker.track_class(Bar)

        foo = Foo()
        bar = Bar()

        self.assertTrue(id(foo) in self.tracker.objects)
        self.assertTrue(id(bar) in self.tracker.objects)

        self.tracker.detach_class(Foo)
        self.tracker.detach_class(Bar)

        foo2 = Foo()
        bar2 = Bar()

        self.assertTrue(id(foo2) not in self.tracker.objects)
        self.assertTrue(id(bar2) not in self.tracker.objects)

        self.assertRaises(KeyError, self.tracker.detach_class, Foo)

    def test_change_name(self):
        """Test modifying name.
        """
        self.tracker.track_class(Foo, name='Foobar')
        self.tracker.track_class(Foo, name='Baz')
        foo = Foo()

        self.assertTrue('Foobar' not in self.tracker.index)
        self.assertTrue('Baz' in self.tracker.index)
        self.assertEqual(self.tracker.index['Baz'][0].ref(),foo)


class TrackerTestCase(unittest.TestCase):

    def test_detach_on_close(self):
        original_constructor = Foo.__init__
        tracker = ClassTracker()
        tracker.track_class(Foo)
        tracker.close()
        self.assertEqual(Foo.__init__, original_constructor)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [TrackObjectTestCase,
                TrackClassTestCase,
                SnapshotTestCase,
                TrackerTestCase
               ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
