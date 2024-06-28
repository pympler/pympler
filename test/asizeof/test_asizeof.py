
import gc
import os
import sys
import unittest
import weakref

import pympler.asizeof as asizeof

from inspect import stack


class Foo(object):
    def __init__(self, content):
        self.data = content

    def __repr__(self):
        return 'Foo'


class ThinFoo(object):
    __slots__ = ('tdata',)
    def __init__(self, content):
        self.tdata = content


class OldFoo:
    def __init__(self, content):
        self.odata = content


class PseudoDict(object):
    '''Dict-like object for inferring dictionaries.'''

    def __len__(self):
        return 0

    def get(self, *args, **kwargs):
        return None

    def has_key(self, *args, **kwargs):
        return False

    def items(self):
        return []

    def keys(self):
        return []

    def values(self):
        return []


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
        asizeof.asizeof(gen, code=True)
        self.assertEqual(next(gen), 1)
        s1 = asizeof.asizeof(gen, code=True)
        self.assertEqual(next(gen), 2)
        s2 = asizeof.asizeof(gen, code=True)
        s3 = asizeof.asizeof(gen, code=False)
        self.assertEqual(next(gen), 3)
        self.assertEqual(s1, s2)
        self.assertNotEqual(s3, 0)

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
        self.assertTrue(asizeof.asizeof(Foo, code=True) > 0)
        self.assertTrue(asizeof.asizeof(ThinFoo, code=True) > 0)
        self.assertTrue(asizeof.asizeof(OldFoo, code=True) > 0)

        self.assertTrue(asizeof.asizeof(Foo([17,42,59])) > 0)
        self.assertTrue(asizeof.asizeof(ThinFoo([17,42,59])) > 0)
        self.assertTrue(asizeof.asizeof(OldFoo([17,42,59])) > 0)

        s1 = asizeof.asizeof(Foo("short"))
        s2 = asizeof.asizeof(Foo("long text ... well"))
        self.assertTrue(s2 >= s1)
        s3 = asizeof.asizeof(ThinFoo("short"))
        self.assertTrue(s3 <= s1)

    def test_special_objects(self):
        '''Test sizing special objects.
        '''
        module_size = asizeof.asizeof(unittest)
        self.assertTrue(module_size > 0, module_size)

    def test_enumerate(self):
        '''Test sizing enumerators.
        '''
        enum = enumerate([1,2,3])
        enum_size = asizeof.asizeof(enum)
        self.assertTrue(enum_size > 0, enum_size)
        refs = asizeof.named_refs(enum)
        ref_names = set([name for name, _ in refs])
        self.assertTrue(set(['__doc__']) <= ref_names, ref_names)

    def test_array(self):
        from array import array
        arr = array('i', [0] * 100)
        arr_size = asizeof.asizeof(arr)
        buf_size = arr.buffer_info()[1] * arr.itemsize
        self.assertTrue(arr_size >= buf_size, (arr_size, buf_size))

    def test_weakref(self):
        '''Test sizing weak references.
        '''
        alive = Foo('alive')
        aref = weakref.ref(alive)
        dead = Foo('dead')
        dref = weakref.ref(dead)
        del dead
        aref_size = asizeof.asizeof(aref)
        self.assertTrue(aref_size > asizeof.asizeof(alive), aref_size)
        refs = asizeof.named_refs(aref)
        # TODO: Should a weakref return ('ref', obj)?
        dref_size = asizeof.asizeof(dref)
        self.assertTrue(dref_size > 0, dref_size)
        self.assertNotEqual(dref_size, aref_size)
        refs = asizeof.named_refs(dref)

    def test_os_stat(self):
        '''Test sizing os.stat and os.statvfs objects.
        '''
        try:
            stat = os.stat(__file__)
        except Exception:
            pass
        else:
            stat_size = asizeof.asizeof(stat)
            self.assertTrue(stat_size > 0, stat_size)
            refs = asizeof.named_refs(stat)
            ref_names = set([name for name, _ in refs])
            self.assertTrue(set(['st_mode', 'st_size', 'st_mtime']) <= ref_names, ref_names)

        try:
            stat = os.statvfs(__file__)
        except Exception:
            pass
        else:
            stat_size = asizeof.asizeof(stat)
            self.assertTrue(stat_size > 0, stat_size)
            refs = asizeof.named_refs(stat)
            ref_names = set([name for name, _ in refs])
            self.assertTrue(set(['f_bsize', 'f_blocks']) <= ref_names, ref_names)

    def test_exception(self):
        '''Test sizing exceptions.
        '''
        try:
            raise Exception("Test exception-sizing.")
        except Exception:
            etype, exc, etb = sys.exc_info()
            try:
                tb_size = asizeof.asizeof(etb)
                self.assertTrue(tb_size > 0, tb_size)
                refs = asizeof.named_refs(etb)
                ref_names = set([name for name, _ in refs])
                self.assertTrue(set(['tb_frame', 'tb_next']) <= ref_names, ref_names)
                ex_size = asizeof.asizeof(etype, exc)
                self.assertTrue(ex_size > 0, ex_size)
            finally:
                del etb

    @unittest.skipIf(sys.version_info < (3, 7), "Known to fail on 3.6 with Numpy installed.")
    def test_ignore_frame(self):
        '''Test whether reference cycles are created
        '''
        gc.collect()
        gc.disable()
        s = asizeof.asizeof(all=True, code=True)
        c = gc.collect()
        # NumPy (and/or other, recent) modules causes some
        # objects to be uncollectable, typically 8 or less
        self.assertTrue(c < 9, '%s ref cycles' % (c,))
        gc.enable()

    def test_closure(self):
        '''Test sizing closures.
        '''
        def outer(x):
            def inner():
                return x
            return inner

        data = [1] * 1000
        closure = outer(data)
        size_closure = asizeof.asizeof(closure, code=True)
        size_data = asizeof.asizeof(data)
        self.assertTrue(size_closure >= size_data, (size_closure, size_data))

    def test_namedtuple(self):
        '''Test values are included but namedtuple __dict__ isn't.
        '''
        from collections import namedtuple
        Point = namedtuple('Point', ['x', 'y'])
        point = Point(x=11, y=22)
        size = asizeof.asized(point, detail=1)
        refs = [ref.name for ref in size.refs]
        self.assertTrue('__dict__' not in refs, refs)
        self.assertTrue('11' in refs, refs)

    def test_numpy_array(self):
        '''Test sizing numpy arrays.
        '''
        try:
            from numpy import arange
        except ImportError:
            pass
        else:
            x = arange(1000)
            size = asizeof.asizeof(x)
            self.assertTrue(size > 1000, size)


class FunctionTest(unittest.TestCase):
    '''Test exposed functions and parameters.
    '''

    def test_asized(self):
        '''Test asizeof.asized()
        '''
        self.assertEqual(list(asizeof.asized(detail=2)), [])
        self.assertRaises(KeyError, asizeof.asized, **{'all': True})
        sized = asizeof.asized(Foo(42), detail=2)
        self.assertEqual(sized.name, 'Foo')
        refs = [ref for ref in sized.refs if ref.name == '__dict__']
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0], sized.get('__dict__'))

        refs = [ref for ref in refs[0].refs if ref.name == '[V] data: 42']
        self.assertEqual(len(refs), 1, refs)
        i = 42
        self.assertEqual(refs[0].size, asizeof.asizeof(i), refs[0].size)
        # Size multiple objects
        sizer = asizeof.Asizer()
        sized_objs = sizer.asized(Foo(3), Foo(4), detail=2)
        self.assertEqual(len(sized_objs), 2)

    def test_asized_detail(self):
        foo = Foo(42)
        size1 = asizeof.asized(foo, detail=1)
        size2 = asizeof.asized(foo, detail=2)
        self.assertEqual(size1.size, size2.size)

    def test_asized_format(self):
        '''Test Asized.format(depth=x)
        '''
        foo = Foo(42)
        sized1 = asizeof.asized(foo, detail=1)
        sized2 = asizeof.asized(foo, detail=2)
        sized1_no = sized1.format('%(name)s', order_by='name')
        sized1_d1 = sized1.format('%(name)s', depth=1, order_by='name')
        sized1_d2 = sized1.format('%(name)s', depth=2, order_by='name')
        sized2_d1 = sized2.format('%(name)s', depth=1, order_by='name')
        sized2_d2 = sized2.format('%(name)s', depth=2, order_by='name')
        self.assertEqual(sized1_no, "Foo\n    __class__\n    __dict__")
        self.assertEqual(sized1_no, sized1_d1)
        self.assertEqual(sized1_no, sized1_d2)
        self.assertEqual(sized1_d1, sized2_d1)
        self.assertNotEqual(sized2_d1, sized2_d2)

    def test_asizesof(self):
        '''Test asizeof.asizesof()
        '''
        self.assertEqual(list(asizeof.asizesof()), [])
        self.assertRaises(KeyError, asizeof.asizesof, **{'all': True})

        objs = [Foo(42), ThinFoo("spam"), OldFoo(67)]
        sizes = list(asizeof.asizesof(*objs))
        objs.reverse()
        rsizes = list(asizeof.asizesof(*objs))
        self.assertEqual(len(sizes), 3)
        rsizes.reverse()
        self.assertEqual(sizes, rsizes, (sizes, rsizes))
        objs.reverse()
        isizes = [asizeof.asizeof(obj) for obj in objs]
        self.assertEqual(sizes, isizes)
        sizer = asizeof.Asizer()
        asizer_sizes = sizer.asizesof(*objs)
        self.assertEqual(list(asizer_sizes), sizes)
        code_sizes = sizer.asizesof(*objs, **dict(code=True))
        self.assertNotEqual(list(code_sizes), sizes)

    def test_asizesof_cyclic_references(self):
        foo = Foo(1)
        bar = Foo(2)

        foo.next = bar
        bar.prev = foo

        sizes = list(asizeof.asizesof(foo, bar))
        self.assertEqual(len(sizes), 2)
        self.assertTrue(all(size > 0 for size in sizes), sizes)
        cycle_size = asizeof.asizeof(foo)
        self.assertEqual(cycle_size, sum(sizes))

    def test_asizeof(self):
        '''Test asizeof.asizeof()
        '''
        self.assertEqual(asizeof.asizeof(), 0)

        objs = [Foo(42), ThinFoo("spam"), OldFoo(67)]
        total = asizeof.asizeof(*objs)
        sizes = list(asizeof.asizesof(*objs))
        sum = 0
        for sz in sizes:
            sum += sz
        self.assertEqual(total, sum, (total, sum))

    def test_asizer_limit(self):
        '''Test limit setting for Asizer.
        '''
        objs = [Foo(42), ThinFoo("spam"), OldFoo(67)]
        sizer = [asizeof.Asizer() for _ in range(4)]
        for limit, asizer in enumerate(sizer):
            asizer.asizeof(objs, limit=limit)
        limit_sizes = [asizer.total for asizer in sizer]
        self.assertTrue(limit_sizes[0] < limit_sizes[1], limit_sizes)
        self.assertTrue(limit_sizes[1] < limit_sizes[2], limit_sizes)
        self.assertTrue(limit_sizes[2] < limit_sizes[3], limit_sizes)

    def test_basicsize(self):
        '''Test asizeof.basicsize()
        '''
        objects = [1, '', 'a', True, None]
        for o in objects:
            self.assertEqual(asizeof.basicsize(o), type(o).__basicsize__)
        objects = [[], (), {}]
        for o in objects:
            self.assertEqual(asizeof.basicsize(o) - asizeof._sizeof_CPyGC_Head,
                type(o).__basicsize__)
        l1 = [1,2,3,4]
        l2 = ["spam",2,3,4,"eggs",6,7,8]
        self.assertEqual(asizeof.basicsize(l1), asizeof.basicsize(l2))

    def test_itemsize(self):
        '''Test asizeof.itemsize()
        '''
        objects = [1, True, None, ()]
        for o in objects:
            self.assertEqual(asizeof.itemsize(o), type(o).__itemsize__)
        itemsizes = [({}, asizeof._sizeof_CPyDictEntry),
                     (set(), asizeof._sizeof_Csetentry),
                     ]
        for o, itemsize in itemsizes:
            self.assertEqual(asizeof.itemsize(o), itemsize)

    def test_leng(self):
        '''Test asizeof.leng()
        '''
        l = [1,2,3,4]
        s = "spam"
        self.assertTrue(asizeof.leng(l) >= len(l), asizeof.leng(l))
        self.assertEqual(asizeof.leng(tuple(l)), len(l))
        self.assertTrue(asizeof.leng(set(l)) >= len(set(l)))
        self.assertTrue(asizeof.leng(s) >= len(s))

        # Python 3.0 ints behave like Python 2.x longs. leng() reports
        # None for old ints and >=1 for new ints/longs.
        self.assertTrue(asizeof.leng(42) in [None, 1], asizeof.leng(42))
        base = 2
        try:
            base = long(base)
        except NameError: # Python3.0
            pass
        self.assertEqual(asizeof.leng(base**8-1), 1)
        self.assertEqual(asizeof.leng(base**16-1), 1)
        self.assertTrue(asizeof.leng(base**32-1) >= 1)
        self.assertTrue(asizeof.leng(base**64-1) >= 2)

    def test_refs(self):
        '''Test asizeof.refs()
        '''
        f = Foo(42)
        refs = list(asizeof.refs(f))
        self.assertTrue(len(refs) >= 1, len(refs))
        self.assertTrue({'data': 42} in refs, refs)

        f = OldFoo(42)
        refs = list(asizeof.refs(f))
        self.assertTrue(len(refs) >= 1, len(refs))
        self.assertTrue({'odata': 42} in refs, refs)

        f = ThinFoo(42)
        refs = list(asizeof.refs(f))
        self.assertTrue(len(refs) >= 2, len(refs))
        self.assertTrue(42 in refs, refs)
        # __slots__ are no longer in refs(anInstance),
        # only the value of the __slots__ attributes
        # /mrJean1 2018-07-05
        # self.assertTrue(('tdata',) in refs, refs)  # slots

    def test_exclude_types(self):
        '''Test Asizer.exclude_types().
        '''
        sizer = asizeof.Asizer()
        sizer.exclude_types(Foo)
        self.assertEqual(sizer.asizeof(Foo('ignored')), 0)

    def test_asizer(self):
        '''Test Asizer properties.
        '''
        sizer = asizeof.Asizer()
        obj = 'unladen swallow'
        mutable = [obj]
        sizer.asizeof(obj)
        self.assertEqual(sizer.total, asizeof.asizeof(obj))
        sizer.asizeof(mutable, mutable)
        self.assertEqual(sizer.duplicate, 2)  # obj seen 3x!
        self.assertEqual(sizer.total, asizeof.asizeof(obj, mutable))

    def test_adict(self):
        '''Test asizeof.adict()
        '''
        pdict = PseudoDict()
        size1 = asizeof.asizeof(pdict)
        asizeof.adict(PseudoDict)
        size2 = asizeof.asizeof(pdict)
        # TODO: come up with useful assertions
        self.assertEqual(size1, size2)

    def test_private_slots(self):
        class PrivateSlot(object):
            __slots__ = ('__data',)
            def __init__(self, data):
                self.__data = data

        data = [42] * 100
        container = PrivateSlot(data)
        size1 = asizeof.asizeof(container)
        size2 = asizeof.asizeof(data)
        self.assertTrue(size1 > size2, (size1, size2))


def _repr(o):
    return repr(o)


class AsizeofDemos(unittest.TestCase):
    '''
    Test consisting of asizeof demos (usage examples).
    Not many asserts are found in here - it merely serves as a full coverage
    test checking if errors occurred while executing the test.
    '''

    MAX = sys.getrecursionlimit()

    class DevNull(object):
        def write(self, text):
            pass

    def setUp(self):
        self._stdout = sys.stdout
        sys.stdout = self.DevNull()

    def tearDown(self):
        sys.stdout = self._stdout

    def _printf(self, *args):
        pass # XXX

    def _print_asizeof(self, obj, infer=False, stats=0):
        a = [_repr(obj),]
        for d, c in ((0, False), (self.MAX, False), (self.MAX, True)):
            a.append(asizeof.asizeof(obj, limit=d, code=c, infer=infer, stats=stats))
        self._printf(" asizeof(%s) is %d, %d, %d", *a)

    def _print_functions(self, obj, name=None, align=8, detail=MAX, code=False, limit=MAX,
                              opt='', **unused):
        if name:
            self._printf('%sasizeof functions for %s ... %s', os.linesep, name, opt)
        self._printf('%s(): %s', ' basicsize', asizeof.basicsize(obj))
        self._printf('%s(): %s', ' itemsize',  asizeof.itemsize(obj))
        self._printf('%s(): %r', ' leng',      asizeof.leng(obj))
        self._printf('%s(): %s', ' refs',     _repr(asizeof.refs(obj)))
        self._printf('%s(): %s', ' flatsize',  asizeof.flatsize(obj, align=align))  # , code=code
        self._printf('%s(): %s', ' asized',           asizeof.asized(obj, align=align, detail=detail, code=code, limit=limit))
      ##_printf('%s(): %s', '.asized',   _asizer.asized(obj, align=align, detail=detail, code=code, limit=limit))

    class C: pass

    class D(dict):
        _attr1 = None
        _attr2 = None

    class E(D):
        def __init__(self, a1=1, a2=2):
            self._attr1 = a1
            self._attr2 = a2

    class P(object):
        _p = None
        def _get_p(self):
            return self._p
        p = property(_get_p)

    class O:  # old style
        a = None
        b = None

    class S(object):  # new style
        __slots__ = ('a', 'b')

    class T(object):
        __slots__ = ('a', 'b')
        def __init__(self):
            self.a = self.b = 0

    def test_all(self):
        '''Test all=True example'''
        self._printf('%sasizeof(limit=%s, code=%s, %s) ... %s', os.linesep, 'self.MAX', True, 'all=True', '-all')
        asizeof.asizeof(limit=self.MAX, code=True, stats=self.MAX, all=True)

    def test_basic(self):
        '''Test basic examples'''
        self._printf('%sasizeof(%s) for (limit, code) in %s ... %s', os.linesep, '<basic_objects>', '((0, False), (MAX, False), (MAX, True))', '-basic')
        for o in (None, True, False,
                  1.0, 1.0e100, 1024, 1000000000,
                  '', 'a', 'abcdefg',
                  {}, (), []):
            self._print_asizeof(o, infer=True)

    def test_class(self):
        '''Test class and instance examples'''
        self._printf('%sasizeof(%s) for (limit, code) in %s ... %s', os.linesep, '<non-callable>', '((0, False), (MAX, False), (MAX, True))', '-class')
        for o in (self.C(), self.C.__dict__,
                  self.D(), self.D.__dict__,
                  self.E(), self.E.__dict__,
                  self.P(), self.P.__dict__, self.P.p,
                  self.O(), self.O.__dict__,
                  self.S(), self.S.__dict__,
                  self.S(), self.S.__dict__,
                  self.T(), self.T.__dict__):
            self._print_asizeof(o, infer=True)

    def test_code(self):
        '''Test code examples'''
        self._printf('%sasizeof(%s) for (limit, code) in %s ... %s', os.linesep, '<callable>', '((0, False), (MAX, False), (MAX, True))', '-code')
        for o in (self.C, self.D, self.E, self.P, self.S, self.T,  # classes are callable
                  type,
                 asizeof._co_refs, asizeof._dict_refs, asizeof._inst_refs, asizeof._len_int, asizeof._seq_refs, lambda x: x,
                (asizeof._co_refs, asizeof._dict_refs, asizeof._inst_refs, asizeof._len_int, asizeof._seq_refs),
                 asizeof._typedefs):
            self._print_asizeof(o)

    def test_dict(self):
        '''Test dict and UserDict examples'''
        self._printf('%sasizeof(%s) for (limit, code) in %s ... %s', os.linesep, '<Dicts>', '((0, False), (MAX, False), (MAX, True))', '-dict')
        try:
            import UserDict  # no UserDict in 3.0
            for o in (UserDict.IterableUserDict(), UserDict.UserDict()):
                self._print_asizeof(o)
        except ImportError:
            pass

        class _Dict(dict):
            pass

        for o in (dict(), _Dict(),
                  self.P.__dict__,  # dictproxy
                  weakref.WeakKeyDictionary(), weakref.WeakValueDictionary(),
                 asizeof._typedefs):
            self._print_asizeof(o, infer=True)

  ##if _opts('-gc'):  # gc examples
      ##_printf('%sasizeof(limit=%s, code=%s, *%s) ...', linesep, 'MAX', False, 'gc.garbage')
      ##from gc import collect, garbage  # list()
      ##asizeof(limit=MAX, code=False, stats=1, *garbage)
      ##collect()
      ##asizeof(limit=MAX, code=False, stats=2, *garbage)

    def test_generator(self):
        '''Test generator examples'''
        self._printf('%sasizeof(%s, code=%s) ... %s', os.linesep, '<generator>', True, '-gen[erator]')
        def gen(x):
            i = 0
            while i < x:
                yield i
                i += 1
        a = gen(5)
        b = gen(50)
        asizeof.asizeof(a, code=True, stats=1)
        asizeof.asizeof(b, code=True, stats=1)
        asizeof.asizeof(a, code=True, stats=1)

    def test_globals(self):
        '''Test globals examples'''
        self._printf('%sasizeof(%s, limit=%s, code=%s) ... %s', os.linesep, 'globals()', 'MAX', False, '-glob[als]')
        asizeof.asizeof(globals(), limit=self.MAX, code=False, stats=1)
        self._print_functions(globals(), 'globals()', opt='-glob[als]')

        self._printf('%sasizesof(%s, limit=%s, code=%s) ... %s', os.linesep, 'globals(), locals()', 'MAX', False, '-glob[als]')
        asizeof.asizesof(globals(), locals(), limit=self.MAX, code=False, stats=1)
        asizeof.asized(globals(), align=0, detail=self.MAX, limit=self.MAX, code=False, stats=1)

    def test_long(self):
        '''Test int and long examples'''
        try:
            _L5d  = long(1) << 64
            _L17d = long(1) << 256
            t = '<int>/<long>'
        except NameError:
            _L5d  = 1 << 64
            _L17d = 1 << 256
            t = '<int>'

        self._printf('%sasizeof(%s, align=%s, limit=%s) ... %s', os.linesep, t, 0, 0, '-int')
        for o in (1024, 1000000000,
                  1.0, 1.0e100, 1024, 1000000000,
                  self.MAX, 1 << 32, _L5d, -_L5d, _L17d, -_L17d):
            self._printf(" asizeof(%s) is %s (%s + %s * %s)", _repr(o), asizeof.asizeof(o, align=0, limit=0),
                                                         asizeof.basicsize(o), asizeof.leng(o), asizeof.itemsize(o))

    def test_iterator(self):
        '''Test iterator examples'''
        self._printf('%sasizeof(%s, code=%s) ... %s', os.linesep, '<iterator>', False, '-iter[ator]')
        o = iter('0123456789')
        e = iter('')
        d = iter({})
        i = iter(asizeof._items({1:1}))
        k = iter(asizeof._keys({2:2, 3:3}))
        v = iter(asizeof._values({4:4, 5:5, 6:6}))
        l = iter([])
        t = iter(())
        asizeof.asizesof(o, e, d, i, k, v, l, t, limit=0, code=False, stats=1)
        asizeof.asizesof(o, e, d, i, k, v, l, t, limit=9, code=False, stats=1)

    def test_locals(self):
        '''Test locals examples'''
        self._printf('%sasizeof(%s, limit=%s, code=%s) ... %s', os.linesep, 'locals()', 'MAX', False, '-loc[als]')
        asizeof.asizeof(locals(), limit=self.MAX, code=False, stats=1)
        self._print_functions(locals(), 'locals()', opt='-loc[als]')

    def test_pairs(self):
        '''Test key pair examples'''
         # <http://jjinux.blogspot.com/2008/08/python-memory-conservation-tip.html>
        self._printf('%sasizeof(%s) vs asizeof(%s) ... %s', os.linesep, 'dict[i][j]', 'dict[(i,j)]', '-pair[s]')
        n = m = 200

        p = {}  # [i][j]
        for i in range(n):
            q = {}
            for j in range(m):
                q[j] = None
            p[i] = q
        p = asizeof.asizeof(p, stats=1)

        t = {}  # [(i,j)]
        for i in range(n):
            for j in range(m):
                t[(i,j)] = None
        t = asizeof.asizeof(t, stats=1)

        self._printf('%sasizeof(dict[i][j]) is %s of asizeof(dict[(i,j)])', os.linesep, asizeof._p100(p, t))

    def test_slots(self):
        '''Test slots examples'''
        self._printf('%sasizeof(%s, code=%s) ... %s', os.linesep, '<__slots__>', False, '-slots')
        class Old:
            pass  # m = None
        class New(object):
            __slots__ = ('n',)
        class Sub(New):
            __slots__ = {'s': ''}  # duplicate!
            def __init__(self):
                New.__init__(self)
         # basic instance sizes
        o, n, s = Old(), New(), Sub()
        asizeof.asizesof(o, n, s, limit=self.MAX, code=False, stats=1)
         # with unique min attr size
        o.o = 'o'
        n.n = 'n'
        s.n = 'S'
        s.s = 's'
        asizeof.asizesof(o, n, s, limit=self.MAX, code=False, stats=1)
         # with duplicate, intern'ed, 1-char string attrs
        o.o = 'x'
        n.n = 'x'
        s.n = 'x'
        s.s = 'x'
        asizeof.asizesof(o, n, s, 'x', limit=self.MAX, code=False, stats=1)
         # with larger attr size
        o.o = 'o'*1000
        n.n = 'n'*1000
        s.n = 'n'*1000
        s.s = 's'*1000
        asizeof.asizesof(o, n, s, 'x'*1000, limit=self.MAX, code=False, stats=1)

    def test_stack(self):
        '''Test stack examples'''
        self._printf('%sasizeof(%s, limit=%s, code=%s) ... %s', os.linesep, 'stack(MAX)[1:]', 'MAX', False, '')
        asizeof.asizeof(stack(self.MAX)[1:], limit=self.MAX, code=False, stats=1)
        self._print_functions(stack(self.MAX)[1:], 'stack(MAX)', opt='-stack')

    def test_sys_mods(self):
        '''Test sys.modules examples'''
        self._printf('%sasizeof(limit=%s, code=%s, *%s) ... %s', os.linesep, 'MAX', False, 'sys.modules.values()', '-sys')
        asizeof.asizeof(limit=self.MAX, code=False, stats=1, *sys.modules.values())
        self._print_functions(sys.modules, 'sys.modules', opt='-sys')

    def test_typedefs(self): # remove?
        '''Test showing all basic _typedefs'''
        t = len(asizeof._typedefs)
        w = len(str(t)) * ' '
        self._printf('%s%d type definitions: basic- and itemsize (leng), kind ... %s', os.linesep, t, '-type[def]s')
        for k, v in sorted((asizeof._prepr(k), v) for k, v in asizeof._items(asizeof._typedefs)):
            s = '%(base)s and %(item)s%(leng)s, %(kind)s%(code)s' % v.format()
            self._printf('%s %s: %s', w, k, s)


if __name__ == '__main__':

    if '-v' in sys.argv[1:]:  # and sys.version_info > (2, 7, 0)
        unittest.main(verbosity=2)
    else:
        unittest.main()

  ##suite = unittest.makeSuite([AsizeofTest, TypesTest, FunctionTest, AsizeofDemos], 'test')
  ##suite.addTest(doctest.DocTestSuite())
  ##suite.debug()
  ##unittest.TextTestRunner(verbosity=1).run(suite)
