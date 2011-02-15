
import doctest
import gc
import unittest

from pympler.muppy import refbrowser

class TreeTest(unittest.TestCase):

    # sample tree used in output tests
    sample_tree = None

    def setUp(self):
        # set up a sample tree with three children, each having
        # five string leaves and some have references to other children
        TreeTest.sample_tree = refbrowser._Node('root')
        branch1 = refbrowser._Node('branch1')
        TreeTest.sample_tree.children.append(branch1)
        branch2 = refbrowser._Node('branch2')
        TreeTest.sample_tree.children.append(branch2)
        branch3 = refbrowser._Node('branch3')
        TreeTest.sample_tree.children.append(branch3)
        branch2.children.append(branch3)
        branch3.children.append(branch1)
        for i in ['a','b','c','d','e']:
            branch1.children.append(i)
            branch2.children.append(i)
            branch3.children.append(i)


    def tearDown(self):
        """Need to delete reference cycles, otherwise test data will affect
        garbage graph tests."""
        gc.collect()


    def test_node(self):
        """Test node functionality.

        _Nodes can be created, linked to each other, and the output function
        should return the expected result.

        """
        # default representation
        n = refbrowser._Node(1)
        expected = str(1)
        self.assert_(str(n) == expected)
        # custom representation
        expected = 'the quick brown fox'
        def foo(o): return expected
        n = refbrowser._Node(1, foo)
        self.assert_(str(n) == expected)
        # attach child
        n.children.append(2)

    def test_get_tree(self):
        """Test reference browser tree representation."""
        #root <- ref1 <- ref11
        #     <- ref11 (already included)
        #     <- ref2 <- ref22
        root = 'root id'
        # the key-value pair is required since Python 2.7/3.1
        # see http://bugs.python.org/issue4688 for details
        ref1 = [root, []]
        ref11 = [ref1, root]
        ref2 = {1: root, 2:[]}
        ref22 = {1: ref2}

        res = refbrowser.RefBrowser(root, repeat=False).get_tree()
        # note that ref11 should not be included due to the repeat argument
        refs = [ref1, ref2]
        children = [c.o for c in res.children if isinstance(c, refbrowser._Node)]
        for r in refs:
            self.assert_(r in children, "%s not in children" % r)
        self.assert_(ref11 not in children)
        # now we test the repeat argument
        res = refbrowser.RefBrowser(root, repeat=True).get_tree()
        refs = [ref1, ref11, ref2]
        children = [c.o for c in res.children if isinstance(c, refbrowser._Node)]
        for r in refs:
            self.assert_(r in children)
        # test if maxdepth is working
        res = refbrowser.RefBrowser(root, maxdepth=0).get_tree()
        self.assertEqual(len(res.children), 0)
        res = refbrowser.RefBrowser(root, maxdepth=1).get_tree()
        for c in res.children:
            if c == ref1:
                self.assertEqual(len(c.children), 0)
        # test if the str_func is applied correctly
        expected = 'the quick brown fox'
        def foo(o): return expected
        res = refbrowser.RefBrowser(root, str_func=foo, maxdepth=2).get_tree()
        self.assertEqual(str(res), expected)
        res = refbrowser.RefBrowser(root, str_func=foo, repeat=True,\
                                    maxdepth=2).get_tree()
        self.assertEqual(str(res), expected)


test_print_tree = """

let's start with a small tree first
>>> crb = refbrowser.ConsoleBrowser(None, maxdepth=1)
>>> crb.print_tree(TreeTest.sample_tree)
root-+-branch1
     +-branch2
     +-branch3

okay, next level
>>> crb = refbrowser.ConsoleBrowser(None, maxdepth=2)
>>> crb.print_tree(TreeTest.sample_tree)
root-+-branch1-+-a
     |         +-b
     |         +-c
     |         +-d
     |         +-e
     |
     +-branch2-+-branch3
     |         +-a
     |         +-b
     |         +-c
     |         +-d
     |         +-e
     |
     +-branch3-+-branch1
               +-a
               +-b
               +-c
               +-d
               +-e

and now full size

>>> crb = refbrowser.ConsoleBrowser(None, maxdepth=4)
>>> crb.print_tree(TreeTest.sample_tree)
root-+-branch1-+-a
     |         +-b
     |         +-c
     |         +-d
     |         +-e
     |
     +-branch2-+-branch3-+-branch1-+-a
     |         |         |         +-b
     |         |         |         +-c
     |         |         |         +-d
     |         |         |         +-e
     |         |         |
     |         |         +-a
     |         |         +-b
     |         |         +-c
     |         |         +-d
     |         |         +-e
     |         |
     |         +-a
     |         +-b
     |         +-c
     |         +-d
     |         +-e
     |
     +-branch3-+-branch1-+-a
               |         +-b
               |         +-c
               |         +-d
               |         +-e
               |
               +-a
               +-b
               +-c
               +-d
               +-e
"""

__test__ = {"test_print_tree": test_print_tree}

def suite():
    suite = unittest.makeSuite(TreeTest,'test')
    suite.addTest(doctest.DocTestSuite())
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

