
import pympler.asizeof as asizeof
import sys
import unittest

if hasattr(sys, 'getsizeof'):

  class AsizeofTest(unittest.TestCase):

    def _failf(self, fmt, *args):
        self.fail(fmt % args)

    def test_flatsize_vs_getsizeof(self):
        '''Test asizeof.flatsize() vs sys.getsizeof()
        '''
         # make sure test function exists
        f = getattr(asizeof, 'test_flatsize')
        self.assert_(f, msg='no asizeof.test_flatsize')
         # run all the tests, report failures
        n, e = f(failf=self._failf)  # stdf=sys.stderr)
         # no tests ran?
        self.assert_(n, msg='zero tests ran in %r' % f)
         # no unexpected failures?
        self.assert_(not e, msg='%s failures in %s tests' % (e, n))

else:

  class AsizeofTest(unittest.TestCase):

    def test_flatsize(self):
        '''Test asizeof.flatsize()
        '''
        l = ["spam",2,3,4,"eggs",6,7,8]
        for _type in (list, tuple, set, frozenset):
            data = _type(l)            
            bsz = asizeof.basicsize(data)
            isz = asizeof.itemsize(data)
            lng = asizeof.leng(data)
            fsz = asizeof.flatsize(data)
            assert fsz == bsz + (lng*isz), (fsz, bsz, lng, isz)

        self.assertRaises(ValueError, asizeof.flatsize, l, **{'align': 3})


class Foo(object):
    def __init__(self, content):
        self.data = content

class ThinFoo(object):
    __slots__ = ['tdata']
    def __init__(self, content):
        self.tdata = content

class OldFoo:
    def __init__(self, content):
        self.odata = content

class TypesTest(unittest.TestCase):

    def test_generator(self):
        '''Test integrity of sized generator
        '''
        def infinite_gen():
            i = 1
            while True:
                yield i
                i += 1    

        gen = infinite_gen()
        s1 = asizeof.asizeof(gen, code=True)
        for i in gen:
            assert i == 1
            break
        for i in gen:
            assert i == 2
            break
        s2 = asizeof.asizeof(gen, code=True)
        s3 = asizeof.asizeof(gen, code=False)
        for i in gen:
            assert i == 3
            break
        assert s1 == s2
        assert s3 == 0

    def test_methods(self):
        '''Test sizing methods and functions
        '''
        def foo():
            pass

        s1 = asizeof.asizeof(self.test_methods, code=True)
        s2 = asizeof.asizeof(TypesTest.test_methods, code=True)
        s3 = asizeof.asizeof(foo, code=True)
        # TODO asserts?

    def test_classes(self):
        '''Test sizing class objects and instances
        '''
        assert asizeof.asizeof(Foo, code=True) > 0
        assert asizeof.asizeof(ThinFoo, code=True) > 0
        assert asizeof.asizeof(OldFoo, code=True) > 0

        assert asizeof.asizeof(Foo([17,42,59])) > 0
        assert asizeof.asizeof(ThinFoo([17,42,59])) > 0
        assert asizeof.asizeof(OldFoo([17,42,59])) > 0

        s1 = asizeof.asizeof(Foo("short"))
        s2 = asizeof.asizeof(Foo("long text ... well"))
        assert s2 >= s1
        s3 = asizeof.asizeof(ThinFoo("short"))
        assert s3 <= s1

class FunctionTest(unittest.TestCase):
    '''Test exposed functions and parameters.
    '''

    def test_asized(self):
        '''Test asizeof.asized()
        '''
        assert list(asizeof.asized(detail=2)) == []
        self.assertRaises(KeyError, asizeof.asized, **{'all': True})
        sized = asizeof.asized(Foo(42), detail=2)
        assert "Foo" in sized.name, sized.name
        refs = [ref for ref in sized.refs if ref.name == '__dict__']
        assert len(refs) == 1
        refs = [ref for ref in refs[0].refs if ref.name == '[V] data: 42']
        assert len(refs) == 1, refs
        i = 42
        assert refs[0].size == asizeof.asizeof(i), refs[0].size

    def test_asizesof(self):
        '''Test asizeof.asizesof()
        '''
        assert list(asizeof.asizesof()) == []
        self.assertRaises(KeyError, asizeof.asizesof, **{'all': True})

        objs = [Foo(42), ThinFoo("spam"), OldFoo(67)]
        sizes = list(asizeof.asizesof(*objs))
        objs.reverse()
        rsizes = list(asizeof.asizesof(*objs))
        assert len(sizes) == 3
        rsizes.reverse()
        assert sizes == rsizes, (sizes, rsizes)
        objs.reverse()
        isizes = [asizeof.asizeof(obj) for obj in objs]
        assert sizes == isizes, (sizes, isizes)
        
    def test_asizeof(self):
        '''Test asizeof.asizeof()
        '''
        assert asizeof.asizeof() == 0
        
        objs = [Foo(42), ThinFoo("spam"), OldFoo(67)]
        total = asizeof.asizeof(*objs)
        sizes = list(asizeof.asizesof(*objs))
        sum = 0
        for sz in sizes:
            sum += sz
        assert total == sum, (total, sum)

    def test_basicsize(self):
        '''Test asizeof.basicsize()
        '''
        l1 = [1,2,3,4]
        l2 = ["spam",2,3,4,"eggs",6,7,8]
        assert asizeof.basicsize(l1) == asizeof.basicsize(l2)
        # TODO

    def test_itemsize(self):
        '''Test asizeof.itemsize()
        '''
        # TODO

    def test_leng(self):
        '''Test asizeof.leng()
        '''
        l = [1,2,3,4]
        s = "spam"
        assert asizeof.leng(l) >= len(l), asizeof.leng(l)
        assert asizeof.leng(tuple(l)) == len(l)
        assert asizeof.leng(set(l)) >= len(set(l))
        assert asizeof.leng(s) >= len(s)

        # TODO Python 3.0 ints behave like Python 2.x longs. leng() reports None
        # for old ints and >=1 for new ints/longs. Perhaps this should be
        # unified?
        assert asizeof.leng(42) in [None, 1], asizeof.leng(42)
        base = 2
        try:
            base = long(base)
        except NameError: # Python3.0
            pass            
        # TODO I don't understand what these numbers actually represent
        assert asizeof.leng(base**8-1) == 1
        assert asizeof.leng(base**16-1) == 1 # 2?
        assert asizeof.leng(base**32-1) == 2 # 4?
        assert asizeof.leng(base**64-1) == 5 # 8?

    def test_refs(self):
        '''Test asizeof.refs()
        '''
        f = Foo(42)
        refs = list(asizeof.refs(f))
        assert len(refs) >= 1, len(refs)
        assert {'data': 42} in refs, refs

        f = OldFoo(42)
        refs = list(asizeof.refs(f))
        assert len(refs) >= 1, len(refs)
        assert {'odata': 42} in refs, refs

        f = ThinFoo(42)
        refs = list(asizeof.refs(f))
        assert len(refs) >= 2, len(refs)
        assert 42 in refs, refs
        assert ('tdata',) in refs, refs # slots

    def test_adict(self):
        '''Test asizeof.adict()
        '''
        # TODO

if __name__ == '__main__':

    suite = unittest.makeSuite([AsizeofTest, TypesTest, FunctionTest], 'test')
  ##suite.addTest(doctest.DocTestSuite())
  ##suite.debug()
    unittest.TextTestRunner(verbosity=1).run(suite)

