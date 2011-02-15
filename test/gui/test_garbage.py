
import gc
import os
import sys
import unittest
from pympler.gui.garbage import *
from pympler.gui.graph import _Edge

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
        gc.collect()
        gc.disable()
        gc.set_debug(gc.DEBUG_SAVEALL)

    def tearDown(self):
        gc.set_debug(0)
        del gc.garbage[:]
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

        gb = GarbageGraph()

        self.assertEqual(gb.count, len(gc.garbage))
        self.assert_(gb.count >= 2, gb.count)

        gfoo = [x for x in gb.metadata if x.id == idfoo]
        self.assertEqual(len(gfoo), 1)
        gfoo = gfoo[0]
        self.assertEqual(gfoo.type, 'Foo')
        self.assert_(gfoo.size > 0, gfoo.size)
        self.assertNotEqual(gfoo.str, '')

        gbar = [x for x in gb.metadata if x.id == idbar]
        self.assertEqual(len(gbar), 1)
        gbar = gbar[0]
        self.assertEqual(gbar.type, 'Bar')
        self.assert_(gbar.size > 0, gbar.size)
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
        subs = list(gb.split())
        self.assertEqual(len(subs), 2)

        fbg = [x for x in subs if x.count == 4][0]
        lig = [x for x in subs if x.count == 1][0]

        self.assert_(isinstance(fbg, GarbageGraph))
        self.assert_(isinstance(lig, GarbageGraph))

        self.assertEqual(len(fbg.edges), 4, fbg.edges)
        self.assertEqual(len(lig.edges), 1, lig.edges)

        self.assert_(_Edge(idl, idl, '') in lig.edges, lig.edges)

        self.assert_(_Edge(idfoo, idfd, '__dict__') in fbg.edges, fbg.edges)
        self.assert_(_Edge(idfd, idbar, 'next') in fbg.edges, fbg.edges)
        self.assert_(_Edge(idbar, idbd, '__dict__') in fbg.edges, fbg.edges)
        self.assert_(_Edge(idbd, idfoo, 'prev') in fbg.edges, fbg.edges)

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

        gb1 = GarbageGraph()
        gb2 = GarbageGraph(reduce=1)

        self.assertEqual(gb1.count, gb2.count)
        self.assert_(len(gb1.metadata) > len(gb2.metadata))

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

        self.assert_(_Edge(idfoo, idfd, '__dict__') in gb.edges, gb.edges)
        self.assert_(_Edge(idfd, idbar, 'next') in gb.edges, gb.edges)
        self.assert_(_Edge(idbar, idbd, '__dict__') in gb.edges, gb.edges)
        self.assert_(_Edge(idbd, idfoo, 'prev') in gb.edges, gb.edges)

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

        self.assert_(_Edge(idfoo, idfd, '__dict__') in gb.edges, gb.edges)
        self.assert_(_Edge(idfd, idbar, 'next') in gb.edges, gb.edges)
        self.assert_(_Edge(idbar, idbd, '__dict__') in gb.edges, gb.edges)
        self.assert_(_Edge(idbd, idfoo, 'prev') in gb.edges, gb.edges)

    def test_uncollectable(self):
        """Test uncollectable object tracking.
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
        self.assertEqual(len(genemy), 1)

    def test_write_graph(self):
        """Test writing graph as text.
        """
        foo = Foo()
        foo.parent = foo

        del foo

        g = GarbageGraph()
        g.write_graph('garbage.dot')
        os.unlink('garbage.dot')

    def test_render(self):
        """Test rendering of graph.
        """
        foo = Foo()
        foo.parent = foo

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
    tclasses = [GarbageTestCase,]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
