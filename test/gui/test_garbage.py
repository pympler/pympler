
import gc
import inspect
import os
import sys
import unittest

from io import StringIO

from pympler.garbagegraph import GarbageGraph, start_debug_garbage, end_debug_garbage
from pympler.refgraph import _Edge


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


class Enemy(object):
    def __del__(self):
        pass


class GarbageTestCase(unittest.TestCase):
    def setUp(self):
        start_debug_garbage()
        gc.set_debug(gc.DEBUG_SAVEALL)

    def tearDown(self):
        end_debug_garbage()
        del gc.garbage[:]

    def test_empty(self):
        """Test empty garbage graph.
        """
        gb = GarbageGraph()
        self.assertEqual(gb.count, 0)
        self.assertEqual(gb.render('garbage.eps'), False)

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

        gb = GarbageGraph()

        self.assertEqual(gb.count, len(gc.garbage))
        self.assertTrue(gb.count >= 2, gb.count)

        gfoo = [x for x in gb.metadata if x.id == idfoo]
        self.assertEqual(len(gfoo), 1)
        gfoo = gfoo[0]
        self.assertEqual(gfoo.type, 'Foo')
        self.assertTrue(gfoo.size > 0, gfoo.size)
        self.assertNotEqual(gfoo.str, '')

        gbar = [x for x in gb.metadata if x.id == idbar]
        self.assertEqual(len(gbar), 1)
        gbar = gbar[0]
        self.assertEqual(gbar.type, 'Bar')
        self.assertTrue(gbar.size > 0, gbar.size)
        self.assertNotEqual(gbar.str, '')

    def test_split(self):
        """Test splitting into subgraphs.
        """
        foo = Foo()
        bar = Bar()

        idfoo = id(foo)
        idbar = id(bar)
        idfd = id(foo.__dict__)
        idbd = id(bar.__dict__)

        foo.next = bar
        bar.prev = foo

        l = []
        l.append(l)
        idl = id(l)

        del foo
        del bar
        del l

        gb = GarbageGraph()
        subs = gb.split_and_sort()
        self.assertEqual(len(subs), 2)

        self.assertEqual(subs[0].count, 4)
        self.assertEqual(subs[1].count, 1)
        fbg, lig = subs

        self.assertTrue(isinstance(fbg, GarbageGraph))
        self.assertTrue(isinstance(lig, GarbageGraph))

        self.assertEqual(len(fbg.edges), 4, fbg.edges)
        self.assertEqual(len(lig.edges), 1, lig.edges)

        self.assertTrue(_Edge(idl, idl, '') in lig.edges, lig.edges)

        self.assertTrue(_Edge(idfoo, idfd, '__dict__') in fbg.edges, fbg.edges)
        self.assertTrue(_Edge(idfd, idbar, 'next') in fbg.edges, fbg.edges)
        self.assertTrue(_Edge(idbar, idbd, '__dict__') in fbg.edges, fbg.edges)
        self.assertTrue(_Edge(idbd, idfoo, 'prev') in fbg.edges, fbg.edges)

    def test_prune(self):
        """Test pruning of reference graph.
        """
        foo = []
        foo.append(foo)
        bar = Bar()
        foo.append(bar)

        idb = id(bar)

        del foo
        del bar

        gb1 = GarbageGraph()
        gb2 = GarbageGraph(reduce=True)

        self.assertEqual(gb1.count, gb2.count)
        self.assertTrue(gb1.count > gb2.num_in_cycles)
        # Only foo should be in the cycle
        self.assertEqual(gb2.num_in_cycles, 1)

        gbar = [x for x in gb1.metadata if x.id == idb]
        self.assertEqual(len(gbar), 1)
        gbar = [x for x in gb2.metadata if x.id == idb]
        self.assertEqual(len(gbar), 0)

    def test_edges_old(self):
        """Test referent identification for old-style classes.
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

        gb = GarbageGraph()

        self.assertTrue(_Edge(idfoo, idfd, '__dict__') in gb.edges, gb.edges)
        self.assertTrue(_Edge(idfd, idbar, 'next') in gb.edges, gb.edges)
        self.assertTrue(_Edge(idbar, idbd, '__dict__') in gb.edges, gb.edges)
        self.assertTrue(_Edge(idbd, idfoo, 'prev') in gb.edges, gb.edges)

    def test_edges_new(self):
        """Test referent identification for new-style classes.
        """
        foo = FooNew()
        bar = BarNew()

        idfoo = id(foo)
        idfd = id(foo.__dict__)
        idbar = id(bar)
        idbd = id(bar.__dict__)

        foo.next = bar
        bar.prev = foo

        del foo
        del bar

        gb = GarbageGraph()

        self.assertTrue(_Edge(idfoo, idfd, '__dict__') in gb.edges, gb.edges)
        self.assertTrue(_Edge(idfd, idbar, 'next') in gb.edges, gb.edges)
        self.assertTrue(_Edge(idbar, idbd, '__dict__') in gb.edges, gb.edges)
        self.assertTrue(_Edge(idbd, idfoo, 'prev') in gb.edges, gb.edges)

    def test_uncollectable(self):
        """Test uncollectable object tracking.

        This is fixed in Python 3.4 (PEP 442).
        """
        foo = Foo()
        foo.parent = foo

        enemy = Enemy()
        enemy.parent = enemy

        idfoo = id(foo)
        idenemy = id(enemy)

        del foo
        del enemy

        gb = GarbageGraph(collectable=0)

        gfoo = [x for x in gb.metadata if x.id == idfoo]
        self.assertEqual(len(gfoo), 0)
        genemy = [x for x in gb.metadata if x.id == idenemy]
        if sys.version_info < (3, 4):
            self.assertEqual(len(genemy), 1)

        self.assertEqual(gb.reduce_to_cycles(), None)

    def test_write_graph(self):
        """Test writing graph as text.
        """
        foo = Foo()
        foo.parent = foo

        del foo

        g = GarbageGraph()
        g.write_graph('garbage.dot')
        os.unlink('garbage.dot')

    def test_print_graph(self):
        """Test writing graph as text.
        """
        foo = Foo()
        foo.parent = foo
        del foo

        out = StringIO()
        GarbageGraph(reduce=True).print_stats(stream=out)
        self.assertTrue('Foo' in out.getvalue(), out.getvalue())

    def test_render(self):
        """Test rendering of graph.
        """
        foo = Foo()
        foo.parent = foo
        foo.constructor = foo.__init__

        def leak_frame():
            frame = inspect.currentframe()

        leak_frame()
        del foo

        g = GarbageGraph()
        try:
            g.render('garbage.eps')
            g.render('garbage.eps', unflatten=True)
        except OSError:
            # Graphviz not installed.
            pass
        else:
            os.unlink('garbage.eps')


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [GarbageTestCase]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
