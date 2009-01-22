import unittest
import gc
import re

from pympler.tracker import ClassTracker
import pympler.process

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

        assert id(foo) in self.tracker.objects
        assert id(bar) in self.tracker.objects

        assert 'Foo' in self.tracker.index
        assert 'Bar' in self.tracker.index

        assert self.tracker.objects[id(foo)].ref() == foo
        assert self.tracker.objects[id(bar)].ref() == bar

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

        assert id(i) not in self.tracker.objects
        assert id(j) not in self.tracker.objects
        assert id(k) not in self.tracker.objects
        assert id(l) not in self.tracker.objects

    def test_track_by_name(self):
        """Test registering objects by name.
        """
        foo = Foo()

        self.tracker.track_object(foo, name='Foobar')

        assert 'Foobar' in self.tracker.index        
        assert self.tracker.index['Foobar'][0].ref() == foo

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

        assert self.tracker.objects[idfoo].ref() is not None
        assert self.tracker.objects[idbar].ref() is None

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

        fp = self.tracker.objects[id(foo)].footprint[-1]
        refs = fp[1].refs
        dref = [r for r in refs if r.name == '__dict__']
        assert len(dref) == 1
        dref = dref[0]
        assert dref.size > 0
        assert dref.flat > 0
        assert dref.refs == ()

        # Test track_change and more fine-grained resolution
        self.tracker.track_change(foo, resolution_level=2)
        self.tracker.create_snapshot()

        fp = self.tracker.objects[id(foo)].footprint[-1]
        refs = fp[1].refs
        dref = [r for r in refs if r.name == '__dict__']
        assert len(dref) == 1
        dref = dref[0]
        namerefs = [r.name for r in dref.refs]
        assert '[K] foo' in namerefs
        assert "[V] foo: 'foo'" in namerefs        

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

        refts = [fp.timestamp for fp in self.tracker.footprint]
        for to in self.tracker.objects.values():
            ts = [t for (t,sz) in to.footprint[1:]]
            assert ts == refts

    def test_snapshot_members(self):
        """Test existence and value of snapshot members.
        """
        foo = Foo()
        self.tracker.track_object(foo)
        self.tracker.create_snapshot()

        fp = self.tracker.footprint[0]
        assert fp.overhead > 0
        assert fp.tracked_total > 0
        assert fp.asizeof_total > 0
        assert fp.asizeof_total >= fp.tracked_total

        if pympler.process.is_available():
            assert fp.system_total.vsz > 0
            assert fp.system_total.rss > 0
            assert fp.system_total.vsz >= fp.system_total.rss 
            assert fp.system_total.vsz > fp.overhead
            assert fp.system_total.vsz > fp.tracked_total
            assert fp.system_total.vsz > fp.asizeof_total

    def test_desc(self):
        """Test footprint description.
        """
        self.tracker.create_snapshot()
        self.tracker.create_snapshot('alpha')
        self.tracker.create_snapshot(description='beta')
        self.tracker.create_snapshot(42)

        assert len(self.tracker.footprint) == 4
        assert self.tracker.footprint[0].desc == ''
        assert self.tracker.footprint[1].desc == 'alpha'
        assert self.tracker.footprint[2].desc == 'beta'
        assert self.tracker.footprint[3].desc == '42'

    def test_background_monitoring(self):
        """Test background monitoring.
        """
        import time

        self.tracker.start_periodic_snapshots(0.1)
        assert self.tracker._periodic_thread.interval == 0.1
        assert self.tracker._periodic_thread.getName() == 'BackgroundMonitor'
        for x in range(10): # try to interfere
            self.tracker.create_snapshot(str(x))
        time.sleep(0.5)
        self.tracker.start_periodic_snapshots(0.2)
        assert self.tracker._periodic_thread.interval == 0.2
        self.tracker.stop_periodic_snapshots()
        assert self.tracker._periodic_thread is None
        assert len(self.tracker.footprint) > 10


class TrackClassTestCase(unittest.TestCase):

    def setUp(self):
        self.tracker = ClassTracker()

    def tearDown(self):
        self.tracker.stop_periodic_snapshots()
        self.tracker.clear()

    def test_track_class(self):
        """Test tracking objects through classes.
        """
        self.tracker.track_class(Foo)
        self.tracker.track_class(Bar)

        foo = Foo()
        bar = Bar()

        assert id(foo) in self.tracker.objects
        assert id(bar) in self.tracker.objects

    def test_track_class_new(self):
        """Test tracking new style classes.
        """
        self.tracker.track_class(FooNew)
        self.tracker.track_class(BarNew)

        foo = FooNew()
        bar = BarNew()

        assert id(foo) in self.tracker.objects
        assert id(bar) in self.tracker.objects

    def test_track_by_name(self):
        """Test registering objects by name.
        """
        self.tracker.track_class(Foo, name='Foobar')

        foo = Foo()

        assert 'Foobar' in self.tracker.index        
        assert self.tracker.index['Foobar'][0].ref() == foo

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

        assert self.tracker.objects[idfoo].ref() is not None
        assert self.tracker.objects[idbar].ref() is None

    def test_detach(self):
        """Test detaching from tracked classes.
        """
        self.tracker.track_class(Foo)
        self.tracker.track_class(Bar)

        foo = Foo()
        bar = Bar()

        assert id(foo) in self.tracker.objects
        assert id(bar) in self.tracker.objects

        self.tracker.detach_class(Foo)
        self.tracker.detach_class(Bar)

        foo2 = Foo()
        bar2 = Bar()
    
        assert id(foo2) not in self.tracker.objects
        assert id(bar2) not in self.tracker.objects

        self.assertRaises(KeyError, self.tracker.detach_class, Foo)

    def test_change_name(self):
        """Test modifying name.
        """
        self.tracker.track_class(Foo, name='Foobar')
        self.tracker.track_class(Foo, name='Baz')
        foo = Foo()

        assert 'Foobar' not in self.tracker.index
        assert 'Baz' in self.tracker.index
        assert self.tracker.index['Baz'][0].ref() == foo


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [ TrackObjectTestCase,
                 TrackClassTestCase,
                 SnapshotTestCase
               ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
