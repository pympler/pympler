import unittest
import gc
import os
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

        assert gb.count == len(gc.garbage)
        assert gb.count >= 2
        
        gfoo = [x for x in gb.metadata if x.id == idfoo]
        assert len(gfoo) == 1
        gfoo = gfoo[0]
        assert gfoo.type == 'Foo'
        assert gfoo.size > 0
        assert gfoo.str != ''

        gbar = [x for x in gb.metadata if x.id == idbar]
        assert len(gbar) == 1
        gbar = gbar[0]
        assert gbar.type == 'Bar'
        assert gbar.size > 0
        assert gbar.str != ''

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
        assert len(subs) == 2

        fbg = [x for x in subs if x.count == 4][0]
        lig = [x for x in subs if x.count == 1][0]

        assert isinstance(fbg, GarbageGraph)
        assert isinstance(lig, GarbageGraph)

        assert len(fbg.edges) == 4, fbg.edges
        assert len(lig.edges) == 1, lig.edges

        assert _Edge(idl, idl, '') in lig.edges, lig.edges

        assert _Edge(idfoo, idfd, '__dict__') in fbg.edges, fbg.edges
        assert _Edge(idfd, idbar, 'next') in fbg.edges, fbg.edges
        assert _Edge(idbar, idbd, '__dict__') in fbg.edges, fbg.edges
        assert _Edge(idbd, idfoo, 'prev') in fbg.edges, fbg.edges

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

        assert gb1.count == gb2.count
        assert len(gb1.metadata) > len(gb2.metadata)
        
        gbar = [x for x in gb1.metadata if x.id == idb]
        assert len(gbar) == 1
        gbar = [x for x in gb2.metadata if x.id == idb]
        assert len(gbar) == 0

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

        assert _Edge(idfoo, idfd, '__dict__') in gb.edges, gb.edges
        assert _Edge(idfd, idbar, 'next') in gb.edges, gb.edges
        assert _Edge(idbar, idbd, '__dict__') in gb.edges, gb.edges
        assert _Edge(idbd, idfoo, 'prev') in gb.edges        

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

        assert _Edge(idfoo, idfd, '__dict__') in gb.edges, gb.edges
        assert _Edge(idfd, idbar, 'next') in gb.edges, gb.edges
        assert _Edge(idbar, idbd, '__dict__') in gb.edges, gb.edges
        assert _Edge(idbd, idfoo, 'prev') in gb.edges        

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
        assert len(gfoo) == 0
        genemy = [x for x in gb.metadata if x.id == idenemy]
        assert len(genemy) == 1

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
        g.render('garbage.eps')
        g.render('garbage.eps', unflatten=True)
        os.unlink('garbage.eps')


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [GarbageTestCase,]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
