#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

import unittest
import gc
import StringIO

from pympler.tracker.heapmonitor import *

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
        detach_all()

    def test_track_object(self):
        """Test object registration.
        """
        foo = Foo()
        bar = Bar()

        track_object(foo)
        track_object(bar)

        assert id(foo) in tracked_objects
        assert id(bar) in tracked_objects

        assert 'Foo' in tracked_index
        assert 'Bar' in tracked_index

        assert tracked_objects[id(foo)].ref() == foo
        assert tracked_objects[id(bar)].ref() == bar

    def test_type_errors(self):
        """Test intrackable objects.
        """
        i = 42
        j = 'Foobar'
        k = [i,j]
        l = {i: j}

        self.assertRaises(TypeError, track_object, i)
        self.assertRaises(TypeError, track_object, j)
        self.assertRaises(TypeError, track_object, k)
        self.assertRaises(TypeError, track_object, l)

        assert id(i) not in tracked_objects
        assert id(j) not in tracked_objects
        assert id(k) not in tracked_objects
        assert id(l) not in tracked_objects

    def test_track_by_name(self):
        """Test registering objects by name.
        """
        foo = Foo()

        track_object(foo, name='Foobar')

        assert 'Foobar' in tracked_index        
        assert tracked_index['Foobar'][0].ref() == foo

    def test_keep(self):
        """Test lifetime of tracked objects.
        """
        foo = Foo()
        bar = Bar()

        track_object(foo, keep=1)
        track_object(bar)
       
        idfoo = id(foo)
        idbar = id(bar)

        del foo
        del bar

        assert tracked_objects[idfoo].ref() is not None
        assert tracked_objects[idbar].ref() is None

    def test_recurse(self):
        """Test recursive sizing and saving of referents.
        """
        foo = Foo()
        bar = Bar()

        track_object(foo, resolution_level=1)
        create_snapshot()

        fp = tracked_objects[id(foo)].footprint[-1]
        refs = fp[1].refs
        dref = [r for r in refs if r.name == '__dict__']
        assert len(dref) == 1
        dref = dref[0]
        assert dref.size > 0
        assert dref.flat > 0
        assert dref.refs == ()

        # Test track_change and more fine-grained resolution
        track_change(foo, resolution_level=2)
        create_snapshot()

        fp = tracked_objects[id(foo)].footprint[-1]
        refs = fp[1].refs
        dref = [r for r in refs if r.name == '__dict__']
        assert len(dref) == 1
        dref = dref[0]
        namerefs = [r.name for r in dref.refs]
        assert '[K] foo' in namerefs
        assert "[V] foo: 'foo'" in namerefs        

class SnapshotTestCase(unittest.TestCase):

    def setUp(self):
        clear()

    def test_timestamp(self):
        """Test timestamp of snapshots.
        """
        foo = Foo()
        bar = Bar()

        track_object(foo)
        track_object(bar)

        create_snapshot()
        create_snapshot()
        create_snapshot()

        refts = [fp.timestamp for fp in footprint]
        for to in tracked_objects.values():
            ts = [t for (t,sz) in to.footprint[1:]]
            assert ts == refts

    def test_desc(self):
        """Test footprint description.
        """
        create_snapshot()
        create_snapshot('alpha')
        create_snapshot(description='beta')
        create_snapshot(42)

        assert len(footprint) == 4
        assert footprint[0].desc == ''
        assert footprint[1].desc == 'alpha'
        assert footprint[2].desc == 'beta'
        assert footprint[3].desc == '42'

    def test_background_monitoring(self):
        """Test background monitoring.
        """
        import pympler.tracker.heapmonitor

        start_periodic_snapshots(0.1)
        assert pympler.tracker.heapmonitor._periodic_thread.interval == 0.1
        assert pympler.tracker.heapmonitor._periodic_thread.getName() is 'BackgroundMonitor'
        for x in xrange(10): # try to interfere
            create_snapshot()
        time.sleep(0.5)
        start_periodic_snapshots(0.2)
        assert pympler.tracker.heapmonitor._periodic_thread.interval == 0.2
        stop_periodic_snapshots()
        assert pympler.tracker.heapmonitor._periodic_thread is None
        assert len(footprint) > 10


class TrackClassTestCase(unittest.TestCase):

    def setUp(self):
        detach_all()

    def test_track_class(self):
        """Test tracking objects through classes.
        """
        track_class(Foo)
        track_class(Bar)

        foo = Foo()
        bar = Bar()

        assert id(foo) in tracked_objects
        assert id(bar) in tracked_objects

    def test_track_class_new(self):
        """Test tracking new style classes.
        """
        track_class(FooNew)
        track_class(BarNew)

        foo = FooNew()
        bar = BarNew()

        assert id(foo) in tracked_objects
        assert id(bar) in tracked_objects

    def test_track_by_name(self):
        """Test registering objects by name.
        """
        track_class(Foo, name='Foobar')

        foo = Foo()

        assert 'Foobar' in tracked_index        
        assert tracked_index['Foobar'][0].ref() == foo

    def test_keep(self):
        """Test lifetime of tracked objects.
        """
        track_class(Foo, keep=1)
        track_class(Bar)

        foo = Foo()
        bar = Bar()
       
        idfoo = id(foo)
        idbar = id(bar)

        del foo
        del bar

        assert tracked_objects[idfoo].ref() is not None
        assert tracked_objects[idbar].ref() is None

    def test_detach(self):
        """Test detaching from tracked classes.
        """
        track_class(Foo)
        track_class(Bar)

        foo = Foo()
        bar = Bar()

        assert id(foo) in tracked_objects
        assert id(bar) in tracked_objects

        detach_class(Foo)
        detach_class(Bar)

        foo2 = Foo()
        bar2 = Bar()
    
        assert id(foo2) not in tracked_objects
        assert id(bar2) not in tracked_objects

        self.assertRaises(KeyError, detach_class, Foo)

    def test_change_name(self):
        """Test modifying name.
        """
        track_class(Foo, name='Foobar')
        track_class(Foo, name='Baz')
        foo = Foo()

        assert 'Foobar' not in tracked_index
        assert 'Baz' in tracked_index
        assert tracked_index['Baz'][0].ref() == foo

class LogTestCase(unittest.TestCase):

    def setUp(self):
        detach_all()

    def test_dump(self):
        """Test serialization of log data.
        """
        foo = Foo()
        foo.data = range(1000)
        bar = Bar()

        track_object(foo, resolution_level=4)
        track_object(bar)

        create_snapshot('Footest')

        f1 = StringIO.StringIO()
        f2 = StringIO.StringIO()

        print_stats(file=f1)

        tmp = StringIO.StringIO()
        dump_stats(tmp, close=0)

        clear()

        stats = MemStats(stream=f2)
        assert stats.tracked_index is None
        assert stats.footprint is None
        tmp.seek(0)
        stats.load_stats(tmp)
        tmp.close()
        assert 'Foo' in stats.tracked_index

        stats.print_stats()
        stats.print_summary()

        assert f1.getvalue() == f2.getvalue()

        # Test sort_stats and reverse_order
        assert stats.sort_stats('size') == stats
        assert stats.sorted[0].classname == 'Foo'
        stats.reverse_order()
        assert stats.sorted[0].classname == 'Bar'
        stats.sort_stats('classname', 'birth')
        assert stats.sorted[0].classname == 'Bar'
        self.assertRaises(ValueError, stats.sort_stats, 'name', 42, 'classn')
        self.assertRaises(NotImplementedError, stats.diff_stats, stats)

        # Test partial printing
        stats.stream = f3 = StringIO.StringIO()
        stats.sort_stats()
        tolen = len(stats.sorted)
        stats.print_stats(filter='Bar',limit=0.5)
        assert len(stats.sorted) == tolen
        stats.print_summary()
        assert f3.getvalue()[:12] == '__main__.Bar'
        assert len(f3.getvalue()) < len(f1.getvalue())

        f1.close()
        f2.close()
        f3.close()


class GarbageTestCase(unittest.TestCase):
    def setUp(self):
        gc.collect()
        gc.disable()
        gc.set_debug(gc.DEBUG_SAVEALL)

    def tearDown(self):
        gc.enable()

    def test_findgarbage(self):
        """Test garbage annotation.
        """
        foo = Foo()
        bar = Bar()

        idfoo = id(foo)
        idbar = id(bar)

        foo.next = bar
        bar.prev = foo

        del foo
        del bar

        cnt, garbage = find_garbage()

        assert cnt == len(gc.garbage)
        assert cnt >= 2
        
        gfoo = [x for x in garbage if x.id == idfoo]
        assert len(gfoo) == 1
        gfoo = gfoo[0]
        assert gfoo.type == 'Foo'
        assert gfoo.size > 0
        assert gfoo.str != ''

        gbar = [x for x in garbage if x.id == idbar]
        assert len(gbar) == 1
        gbar = gbar[0]
        assert gbar.type == 'Bar'
        assert gbar.size > 0
        assert gbar.str != ''

    def test_noprune(self):
        """Test pruning of reference graph.
        """
        foo = Foo()
        bar = Bar()

        foo.parent = foo
        foo.leaf = bar

        idb = id(bar)

        del foo
        del bar

        cnt1, garbage1 = find_garbage(prune=0)
        cnt2, garbage2 = find_garbage(prune=1)

        assert cnt1 == cnt2
        assert len(garbage1) > len(garbage2)
        
        gbar = [x for x in garbage1 if x.id == idb]
        assert len(gbar) == 1
        gbar = [x for x in garbage2 if x.id == idb]
        assert len(gbar) == 0

    def test_edges(self):
        """Test referent identification.
        """
        foo = Foo()
        bar = Bar()

        idfoo = id(foo)
        idfd = id(foo.__dict__)
        idbar = id(bar)
        idbd = id(bar.__dict__)

        foo.next = bar
        bar.prev = foo

        del foo
        del bar

        gc.collect()
        e = get_edges(gc.garbage[:])

        # TODO: insert labels when implemented
        assert (idfoo, idfd, '') in e
        assert (idfd, idbar, '') in e
        assert (idbar, idbd, '') in e
        assert (idbd, idfoo, '') in e        

if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [ TrackObjectTestCase,
                 TrackClassTestCase,
                 SnapshotTestCase,
                 GarbageTestCase,
                 LogTestCase
               ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
