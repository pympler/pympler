#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright, license and disclaimer are at the very end of this file.

# This is the latest, enhanced version of the asizeof.py recipes at
# <http://GitHub.com/ActiveState/code/blob/master/recipes/Python/
#         546530_Size_of_Python_objects_revised/recipe-546530.py>,
# <http://Code.ActiveState.com/recipes/546530-size-of-python-objects-revised>
# and <http://Code.ActiveState.com/recipes/544288-size-of-python-objects>.

# Note, objects like ``namedtuples``, ``closure``, and NumPy data
# ``array``, ``memmap``, ``ndarray``, etc. are only handled by recent
# versions of this module.  Sizing of ``array.array``, ``int`` and
# ``__slots__`` have been incorrect and property ``Asizer.duplicate``
# gave incorrect values in previous versions.  Several other properties
# have been added to class ``Asizer`` and the ``print_summary`` method
# has been updated.

'''
This module exposes 10 functions and 2 classes to obtain lengths and
sizes of Python objects (for Python 3.6 or later).

Earlier versions of this module supported Python versions down to
Python 2.2.  If you are using Python 3.5 or older, please consider
downgrading Pympler.

**Public Functions** [#unsafe]_

   Function **asizeof** calculates the combined (approximate) size
   in bytes of one or several Python objects.

   Function **asizesof** returns a tuple containing the (approximate)
   size in bytes for each given Python object separately.

   Function **asized** returns for each object an instance of class
   **Asized** containing all the size information of the object and
   a tuple with the referents [#refs]_.

   Functions **basicsize** and **itemsize** return the *basic-*
   respectively *itemsize* of the given object, both in bytes.  For
   objects as ``array.array``, ``numpy.array``, ``numpy.ndarray``,
   etc. where the item size varies depending on the instance-specific
   data type, function **itemsize** returns that item size.

   Function **flatsize** returns the *flat size* of a Python object
   in bytes defined as the *basic size* plus the *item size* times
   the *length* of the given object.

   Function **leng** returns the *length* of an object, like standard
   function ``len`` but extended for several types.  E.g. the **leng**
   of a multi-precision int (formerly long) is the number of ``digits``
   [#digit]_.  The length of most *mutable* sequence objects includes
   an estimate of the over-allocation and therefore, the **leng** value
   may differ from the standard ``len`` result.  For objects like
   ``array.array``, ``numpy.array``, ``numpy.ndarray``, etc. function
   **leng** returns the proper number of items.

   Function **refs** returns (a generator for) the referents [#refs]_
   of the given object.

   Certain classes are known to be sub-classes of or to behave as
   ``dict`` objects.  Function **adict** can be used to register
   other class objects to be treated like ``dict``.

**Public Classes** [#unsafe]_

   Class **Asizer** may be used to accumulate the results of several
   **asizeof** or **asizesof** calls.  After creating an **Asizer**
   instance, use methods **asizeof** and **asizesof** as needed to
   size any number of additional objects.

   Call methods **exclude_refs** and/or **exclude_types** to exclude
   references to respectively instances or types of certain objects.

   Use one of the **print\\_...** methods to report the statistics.

   An instance of class **Asized** is returned for each object sized
   by the **asized** function or method.

**Duplicate Objects**

   Any duplicate, given objects are sized only once and the size
   is included in the accumulated total only once.  But functions
   **asizesof** and **asized** will return a size value respectively
   an **Asized** instance for each given object, including duplicates.

**Definitions** [#arb]_

   The *length* of an objects like ``dict``, ``list``, ``set``,
   ``str``, ``tuple``, etc. is defined as the number of items held
   in or allocated by the object.  Held items are *references* to
   other objects, called the *referents*.

   The *size* of an object is defined as the sum of the *flat size*
   of the object plus the sizes of any referents [#refs]_.  Referents
   are visited recursively up to the specified detail level.  However,
   the size of objects referenced multiple times is included only once
   in the total *size*.

   The *flat size* of an object is defined as the *basic size* of the
   object plus the *item size* times the number of allocated *items*,
   *references* to referents.  The *flat size* does include the size
   for the *references* to the referents, but not the size of the
   referents themselves [#md].

   The *flat size* returned by function *flatsize* equals the result
   of function *asizeof* with options *code=True*, *ignored=False*,
   *limit=0* and option *align* set to the same value.

   The accurate *flat size* for an object is obtained from function
   ``sys.getsizeof()`` where available.  Otherwise, the *length* and
   *size* of sequence objects as ``dicts``, ``lists``, ``sets``, etc.
   is based on an estimate for the number of allocated items.  As a
   result, the reported *length* and *size* may differ substantially
   from the actual *length* and *size*.

   The *basic* and *item size* are obtained from the ``__basicsize__``
   respectively ``__itemsize__`` attributes of the (type of the)
   object.  Where necessary (e.g. for sequence objects), a zero
   ``__itemsize__`` is replaced by the size of a corresponding C type.

   The overhead for Python's garbage collector (GC) is included in
   the *basic size* of (GC managed) objects as well as the space
   needed for ``refcounts`` (used only in certain Python builds).

   Optionally, size values can be aligned to any power-of-2 multiple.

**Size of (byte)code**

   The *(byte)code size* of objects like classes, functions, methods,
   modules, etc. can be included by setting option *code=True*.

   Iterators are handled like sequences: iterated object(s) are sized
   like *referents* [#refs]_, but only up to the specified level or
   recursion *limit* (and only if function ``gc.get_referents()``
   returns the referent object of iterators).

   Generators are sized as *(byte)code* only, but the objects are
   never generated and never sized.

**New-style Classes**

   All ``class``, instance and ``type`` objects are handled uniformly
   such that instance objects are distinguished from class objects.

   Class and type objects are represented as ``<class .... def>``
   respectively ``<type ... def>`` where the ``... def`` suffix marks
   the *definition object*.  Instances of  classes are shown as
   ``<class module.name>`` without the ``... def`` suffix.

**Ignored Objects**

   To avoid excessive sizes, several object types are ignored [#arb]_
   by default, e.g. built-in functions, built-in types and classes
   [#bi]_, function globals and module referents.  However, any
   instances thereof and module objects will be sized when passed as
   given objects.  Ignored object types are included unless option
   *ignored* is set accordingly.

   In addition, many ``__...__`` attributes of callable objects are
   ignored [#arb]_, except crucial ones, e.g. class attributes ``__dict__``,
   ``__doc__``, ``__name__`` and ``__slots__``.  For more details, see
   the type-specific ``_..._refs()`` and ``_len_...()`` functions below.

.. rubric:: Footnotes
.. [#unsafe] The functions and classes in this module are not thread-safe.

.. [#refs] The *referents* of an object are the objects referenced *by*
     that object.  For example, the *referents* of a ``list`` are the
     objects held in the ``list``, the *referents* of a ``dict`` are
     the key and value objects in the ``dict``, etc.

.. [#arb] These definitions and other assumptions are rather arbitrary
     and may need corrections or adjustments.

.. [#digit] The C ``sizeof(digit)`` in bytes can be obtained from the
     ``int.__itemsize__``  attribute or since Python 3.1+  also from
     attribute ``sys.int_info.sizeof_digit``.  Function **leng**
     determines the number of ``digits`` of a multi-precision int.

.. [#bi] All ``type``s and ``class``es in modules named in private set
     ``_ignored_modules`` are ignored like other, standard built-ins.

.. [#md] Since Python 3.13, objects may contain *inline values* and a
     *materialized dict*.  The approximate size of the *inline values*
     references ("slots") is included in the *flatsize* of the object.
     The *materialized dict* will be sized only if present in the object,
     otherwise the *inline values* are sized.  This may need further
     adjustments for Python 3.14 and beyond.
'''  # PYCHOK escape
import sys
if sys.version_info < (3, 6):
    raise NotImplementedError('%s requires Python 3.6 or newer: %s' %
                              (__file__, sys.version.split()[0]))
import gc
import types as Types
import weakref as Weakref

# from abc import ABCMeta
from array import array as _array  # array type
from inspect import (isbuiltin, isclass, iscode, isframe,
                     isfunction, ismethod, ismodule)  # stack
from math import log
from os import curdir, linesep as _NL, environ  # deleted below
# from typing import Callable, Dict, List, Set, Union
from warnings import warn

__all__ = ()  # extended below
__version__ = '25.07.17'  # 24.11.22, 23.11.15, 22.12.07, 22.06.30

_Bools     = (True, False)
_NN        =  \
_Non_vari  = ''  # non-variable item size
_NoneNone  = (None, None)  # not a class
_typeof    =  type  # function
_Type_type = _typeof(type)  # == type and (new-style) class type
_3_Udict   = (3, 9)  # PyDictUnicodeEntry since (3, 6)?
# 'cell' is holding data used in closures
t = (lambda unused: (lambda: unused))(None)
_cell_type = _typeof(t.__closure__[0])  # type: ignore

# Any classes and types in modules named in set _ignored_modules
# are ignored by default, like most built-ins classes and types
_ignored_modules = {Exception.__module__, int.__module__, 'ctypes',
                    isclass.__module__, warn.__module__, '_ctypes',
                    sys.__name__, Types.__name__,  # Weakref.__name__,
                    __name__}  # this very module
try:
    _withGIL = sys._is_gil_enabled  # CPy 3.13+
    if not _withGIL():
        raise NotImplementedError('%s without GIL enabled' % (__file__,))
except AttributeError:
    def _withGIL():
        return True


def property_RO(method):  # XXX class
    '''Immutable, *Read-Only* property.
    '''
    def fget(inst, *unused):  # PYCHOK 2 vs 3 args
        return method(inst)

    def ferr(inst, *unused):  # PYCHOK no cover
        t = _typeof(inst).__name__, method.__name__, inst
        raise TypeError('%s.%s immutable: %r' % t)

    return property(fget, ferr, ferr, method.__doc__)


class _TPFLAGS(object):  # PYCHOK Some Py_TPFLAGS_... in typ.__flags__
    # <https://GitHub.com/python/cpython/blob/main/Include/internal/object.h>

    def __init__(self):
        self.INLINE_VALUES = 1 <<  2  # Py_TPFLAGS_INLINE_VALUES
        self.MANAGED_DICT  = 1 <<  4  # Py_TPFLAGS_MANAGED_DICT
        self.HEAPTYPE      = 1 <<  9  # Py_TPFLAGS_HEAPTYPE
        self.HAVE_GC       = 1 << 14  # Py_TPFLAGS_HAVE_GC

    def inlined(self, typ):
        '''Does a type have *inline values*?
        '''
        f = getattr(typ, '__flags__', 0)
        return bool(f & self.INLINE_VALUES)

    def managed(self, typ):
        '''Does a type have a *managed dict*?
        '''
        f = getattr(typ, '__flags__', 0)
        return bool(f & self.MANAGED_DICT) and \
               bool(f & self.INLINE_VALUES)

_TPFLAGS = _TPFLAGS()  # PYCHOK singleton


class _Sizeof(object):  # PYCHOK sizes of needed C types
    from struct import calcsize  # type/class Struct in CPy 2.5+

    def __init__(self):
        self.Cbyte  = self.calcsize('c')  # sizeof(unsigned char)
        self.Clong  = self.calcsize('l')  # sizeof(long)
        self.Cvoidp = self.calcsize('P')  # sizeof(void*), sizeof(PyObject*)
        try:
            _ = self.calcsize('n')  # CPy 3.3+
            self._z2n = 'n'  # Py_ssize_t
        except Exception:  # struct.error
            # sizeof(long) != sizeof(Py_ssize_t) on LLP64
            self._z2n = 'P' if self.Cvoidp > self.Clong else 'L'

        if sys.version_info < _3_Udict:  # Older basic sizes with 'z' for Py_ssize_t
            self.CPyCodeObject   = self.zsize('Pz10P5i0P')
            self.CPyDictKeyEntry = \
            self.CPyDictStrEntry = self.zsize('z2P')  # z for hash
            self.CPyFrameObject  = self.zsize('Pzz13P63i0P')
            # sizeof(PyGC_Head) should be aligned to sizeof(long double),
            # but there's no way to obtain that size, assume twice double
            self.CPyGC_Head      = self.align(self.zsize('2Pz'),
                                   self.mask( self.zsize('2d')))
            self.CPyModuleObject = self.zsize('PzP0P') + self.CPyDictStrEntry
            self.Csetentry       = self.zsize('lP')
        else:  # <https://GitHub.com/python/cpython/blob/main/Include/internal/...h>
            self.CPyCodeObject   = self.zsize('3PiPi5P4iP')  # PyCodeConstructor
            self.CPyDictKeyEntry = self.zsize('z2P')  # .../internal/pycore_dict.h
            self.CPyDictStrEntry = self.zsize('2P')   # PyDictUnicodeEntry
            self.CPyFrameObject  = self.zsize('3Pi2c4P')
            self.CPyGC_Head      = self.zsize('2P') if _withGIL() else 0  # .../internal/pycore_interp_structs.h
            self.CPyModuleObject = self.zsize('5P') + self.CPyDictStrEntry
            self.Csetentry       = self.zsize('Pl')

        # <https://GitHub.com/python/cpython/.../Lib/_pyrepl/simple_interact.py>
        self.Crefcounts = self.zsize('2z') if hasattr(sys, 'gettotalrefcount') else 0  # _is_debug_build

        # char size for internal unicode in CPy 3.2-
        t = '\0'.encode('utf-8')
        self.Cunicode = len(t)

        # <https://GitHub.com/python/cpython/blob/main/Include/internal/pycore_object.h>
        # <https://GitHub.com/python/cpython/blob/main/Objects/object_layout.md>
        f = -(3 if _withGIL() else 1)  # NOT tested without GIL!
        self.CMdDictOffset = self.Cvoidp * f  # MANAGED_DICT_OFFSET, negative!
        self.CValuesFlags  = self.Cbyte  * 4  # capacity, size, embedded, valid

    def align(self, size, mask):
        '''Align a size to a mask.
        '''
        if mask and size:
            size +=  mask
            size &= ~mask
#           if (mask + 1) & mask:
#               raise _optionError(self.align, mask=mask)
        return size

    amapped = 0.01  # 0 <= percentage <= 1.0
    get     = sys.getsizeof  # in CPy 2.6+

    def inlined(self, obj):
        '''Get an object's *inline* size in bytes: flags and "slots" only!
        '''
        n = _inlined(obj)
        return 0 if n is None else (n * self.Cvoidp + self.CValuesFlags)

    def mask(self, align):
        '''Return the mask for an alignment.
        '''
        if align > 1:
            mask = align - 1
            if mask & align:
                raise _optionError(self.mask, align=align)
        else:
            mask = 0  # don't align
        return mask

    def zsize(self, fmt):
        '''Like struct.calcsize() but with 'z' for Py_ssize_t.
        '''
        # len(pack(T, 0)) == Struct(T).size == calcsize(T)
        return self.calcsize(fmt.replace('z', self._z2n))

_sizeof = _Sizeof()  # PYCHOK singleton

if sys.version_info < _3_Udict:
    _Udict = None

    def _udictof(typ, unused):
        return typ

else:  # CPy _3_Udict+
    # <https://github.com/python/cpython/blob/main/Objects/dictobject.c>
    # <https://github.com/python/cpython/blob/main/Include/cpython/dictobject.h>
    # <https://GitHub.com/python/cpython/blob/main/Objects/dictobject.c>

    class _Udict(dict):  # dict with all (unicode) str keys
        pass

    def _udictof(typ, obj):
        '''Return the type or _Udict.
        '''
        if typ is dict or isinstance(obj, dict):
            # it's too messy to detect the DK_KIND_UNICODE item
            # *PyDictObject.PyDictKeysObject.dk_kind*, instead
            # check that all dict keys are a (unicode) str
            if all(map(_ukey, _keys(obj))):
                typ = _Udict
        return typ

    def _ukey(key):
        '''Is key a (unicode) str?
        '''
        return _typeof(key) is str  # or isinstance(key, str)

if sys.version_info < (3, 13):  # MCCABE 20
    _Inline0 = None

    def _inlined(unused):
        return None  # always

    def _materializedictuple(obj, **unused):
        try:  # the __dict__, always
            return obj.__dict__
        except AttributeError:
            return None

else:  # CPy 3.13+
    # courtesy ArieBovenberg <https://GitHub.com/pympler/pympler/issues/170>,
    # <https://GitHub.com/python/cpython/pull/128763#discussion_r2130003738> and
    # <https://GitHub.com/ariebovenberg/slotscheck/issues/112#issuecomment-2965388559>
    import ctypes as _ct

    class _Inline0(tuple):  # 0-size container of *inline* values or attributes
        pass

    def _inlined(obj):
        '''Return the number of *inline values* or None.
        '''
        r = _materializedictuple(obj, inlinattrs=True)
        return len(r) if _typeof(r) is _Inline0 else None

    def _materializedictuple(obj, inlinattrs=False):
        '''Get the *materialized dict* if present, otherwise a tuple
           with the *inline values* or attributes.
        '''
        try:
            t = _typeof(obj)
            b =  t.__dictoffset__
            if b > 0:  # normal __dict__
                return obj.__dict__
            elif b and _TPFLAGS.managed(t):  # b == -1
                # if present, get the materialized __dict__
                if _void_p_value(id(obj) + _sizeof.CMdDictOffset):
                    r = obj.__dict__
                    # assert len(r) >= len(t.__static_attributes__)
                elif inlinattrs:  # otherwise the inline attrs as tuple
                    r = _Inline0(t.__static_attributes__)
                else:  # or the inline values as tuple
                    def _iv(a):  # doesn't materialize the __dict__
                        return getattr(obj, a, None)
                    # the __static_attributes__ tuple doesn't include
                    # class attrs nor dynamically added instance attrs
                    # <https://GitHub.com/python/cpython/issues/135428>
                    # <https://GitHub.com/python/cpython/issues/123860>
                    r = _Inline0(map(_iv, t.__static_attributes__))
                return r
        except (AttributeError, ValueError):
            pass  # no __dictoffset__, __flags__, __dict__, etc.
        return None

    def _void_p_value(addr):  # deref a c_void_p addr
        return _ct.cast(addr, _ct.POINTER(_ct.c_void_p)).contents.value


# Compatibility functions for more uniform
# behavior across CPy 2.2 thru 3+

def _items(obj):  # dict only
    '''Return iter-/generator, preferably.
    '''
    o = getattr(obj, 'iteritems', obj.items)
    return o() if callable(o) else (o or ())


def _keys(obj):  # dict only
    '''Return iter-/generator, preferably.
    '''
    o = getattr(obj, 'iterkeys', obj.keys)
    return o() if callable(o) else (o or ())


def _values(obj):  # dict only
    '''Return iter-/generator, preferably.
    '''
    o = getattr(obj, 'itervalues', obj.values)
    return o() if callable(o) else (o or ())


# Private functions

def _basicsize(typ, base=0, heap=False, obj=None):
    '''Get non-zero basicsize of type,
       including the header sizes.
    '''
    s = max(getattr(typ, '__basicsize__', 0), base)
    # include gc header size
    if typ != _Type_type:
        f = getattr(typ, '__flags__', 0) & _TPFLAGS.HAVE_GC
    elif heap:  # type, allocated on heap
        f = True
    else:  # None has no __flags__ attr
        f = getattr(obj, '__flags__', 0) & _TPFLAGS.HEAPTYPE
    if f:
        s += _sizeof.CPyGC_Head
    # include reference counter
    return s + _sizeof.Crefcounts


def _classof(obj, dflt=None):
    '''Return the object's class object.
    '''
    return getattr(obj, '__class__', dflt)


def _derive_typedef(typ):
    '''Return single, existing super type typedef or None.
    '''
    v = [v for v in _values(_typedefs) if _issubclass(typ, v.type)]
    return v[0] if len(v) == 1 else None


def _dir2(obj, pref=_NN, excl=(), slots=None, itor=_NN):
    '''Return an attribute (name, object) 2-tuple for certain
       attributes or for the ``__slots__`` attributes of the
       given object, but not both.  Any iterator referent
       objects are returned with the given name if the
       latter is non-empty.
    '''
    if slots:  # __slots__ attrs
        if hasattr(obj, slots):
            # collect all inherited __slots__ attrs
            # from list, tuple, or dict __slots__,
            # while removing any duplicate attrs
            s = {}
            for c in _typeof(obj).mro():  # [:-1]
                n = _nameof(c)
                for a in getattr(c, slots, ()):
                    if a.startswith('__'):
                        a = '_' + n + a
                    if hasattr(obj, a):
                        s.setdefault(a, getattr(obj, a))
            # assume __slots__ tuple-like is holding the values
            # yield slots, _Slots(s)  # _keys(s) ... REMOVED,
            # see _Slots.__doc__ further below
            for t in _items(s):
                yield t  # attr name, value
    elif itor:  # iterator referents
        for o in obj:  # iter(obj)
            yield itor, o
    else:  # regular attrs
        for a in dir(obj):
            if a.startswith(pref) and a not in excl \
                                  and hasattr(obj, a):  # last!
                yield a, getattr(obj, a)


def _infer_dict(obj):
    '''Return True for likely dict object via duck typing.
    '''
    for attrs in (('items', 'keys', 'values'),
                  ('iteritems', 'iterkeys', 'itervalues')):
        attrs += '__len__', 'get'  # 'has_key', 'popitem', 'setdefault', 'update'
        if all(callable(getattr(obj, a, None)) for a in attrs):
            return True
    return False


# def _inlined() ... see above


def _isbuiltin2(typ):
    '''Return True for built-in types as in CPy 2.
    '''
    # range is no longer a built-in in CPy 3+
    return isbuiltin(typ) or (typ is range)


def _iscell(obj):
    '''Return True if obj is a cell as used in a closure.
    '''
    return isinstance(obj, _cell_type)


def _isdictype(obj):
    '''Return True for known dict objects.
    '''
    c = _classof(obj)
    n = _nameof(c)
    return n and n in _dict_types.get(_moduleof(c), ())


def _isframe(obj):
    '''Return True for a stack frame object.
    '''
    try:  # safe isframe(), see pympler.muppy
        return isframe(obj)
    except ReferenceError:
        return False


def _isignored(typ):
    '''Is this a type or class to be ignored?
    '''
    return _moduleof(typ) in _ignored_modules


def _isnamedtuple(obj):
    '''Named tuples are identified via duck typing:
       <http://www.Gossamer-Threads.com/lists/python/dev/1142178>
    '''
    return isinstance(obj, tuple) and hasattr(obj, '_fields')


def _issubclass(obj, Super):
    '''Safe inspect.issubclass() returning None if Super is
       *object* or if obj and Super are not a class or type.
    '''
    if Super is not object:
        try:
            return issubclass(obj, Super)
        except TypeError:
            pass
    return None


def _itemsize(typ, item=0):
    '''Get non-zero itemsize of type.
    '''
    # replace zero value with default
    return getattr(typ, '__itemsize__', 0) or item


def _itemstr(item):
    '''Return a (key, value) pair as str.
    '''
    return '%s=%r' % item


def _kwdstr(**kwds):
    '''Keyword arguments as a string.
    '''
    t = sorted(map(_itemstr, _items(kwds)), key=str.lower)
    return ', '.join(t)


def _lengstr(obj):
    '''Object length as a string.
    '''
    n = leng(obj)
    if n is None:  # no len
        r = _NN
    else:
        x = '!' if n > _len(obj) else _NN  # extended
        r = ' leng %d%s' % (n, x)
    return r


# def _materializedictuple() ... see above


def _moduleof(obj, dflt=_NN):
    '''Return the object's module name.
    '''
    return getattr(obj, '__module__', dflt)


def _nameof(obj, dflt=_NN):
    '''Return the name of an object.
    '''
    return getattr(obj, '__name__', dflt)


if sys.platform == 'ios':  # Apple iOS
    _ignored_modules |= {'objc_util',}  # 'runtime'

    def _None(obj):  # prevent asizeof(all=True, ...) crash:
        # sizing gc.get_objects() crashes in Pythonista3 with
        # CPy 3.5.1 on iOS due to 1-tuple (<Null>,) object, see
        # <http://forum.omz-software.com/user/mrjean1>.
        if isinstance(obj, tuple) and len(obj) == 1 \
                                  and repr(obj) == '(<NULL>,)':
            obj = None  # (None,)
        return obj

    def _noNULLs(lt):
        if isinstance(lt, list):
            lt[:] = map(_None, lt)
        else:
            lt = tuple(map(_None, lt))
        return lt
else:
    def _noNULLs(lt):
        return lt


def _objs_opts_x(where, objs, all=None, **opts):
    '''Return the given or 'all' objects plus
       the remaining options and exclude flag
    '''
    if objs:  # given objects
        t, x = objs, False
    elif all in (False, None):
        t, x = (), True
    elif all is True:  # 'all' objects
        t, x = _noNULLs(gc.get_objects()), True
    else:
        raise _optionError(where, all=all)
    return t, opts, x


def _optionError(where, Error=ValueError, **options):
    '''Format an *Error* instance for invalid *option* or *options*.
    '''
    t = _plural(len(options)), _nameof(where), _kwdstr(**options)
    return Error('invalid option%s: %s(%s)' % t)


def _p100(part, total, prec=1):
    '''Return percentage as string.
    '''
    t = float(total)
    if t > 0:
        p = part * 100.0 / t
        r = '%.*f%%' % (prec, p)
    else:
        r = 'n/a'
    return r


def _plural(num):
    '''Return 's' if *num* is not 1.
    '''
    return 's' if num != 1 else _NN


def _power_of_2(n):
    '''Find the next power of 2.
    '''
    p2 = 2**int(log(n, 2))
    while n > p2:
        p2 += p2
    return p2


def _prepr(obj, clip=0):
    '''Prettify and clip long repr() string.
    '''
    return _repr(obj, clip=clip).strip('<>').replace("'", _NN)  # remove <''>


def _printf(fmt, *args, **end_file_flush):
    '''Formatted print to *sys.stdout* or given stream.

       *end_file_flush* -- some keyword arguments, like Python 3+ print.
    '''
    if args:
        fmt %= args
    if end_file_flush:  # like CPy 3+

        def _opt3(end=_NL, file=None, flush=False, **unused):
            return end, (file or sys.stdout), flush

        e, s, f = _opt3(**end_file_flush)
        s.write(fmt)
        s.write(e)
        if f:
            s.flush()
    else:
        print(fmt)


def _refs(obj, named, *attrs, **kwds):
    '''Return specific attribute objects of an object.
    '''
    if named:
        _N = _NamedRef
    else:
        def _N(unused, o):
            return o

    for a in attrs:  # cf. inspect.getmembers()
        if hasattr(obj, a):
            yield _N(a, getattr(obj, a))
    mdict, kwds = _refs2(obj, **kwds)
    if mdict:  # __dict__ last attr
        # '__dict__' if isinstance(mdict, dict) else '__inlined__'
        yield _N('__dict__', mdict)
    if kwds:  # kwds are _dir2() args
        for a, o in _dir2(obj, **kwds):
            yield _N(a, o)


def _refs2(obj, mdict=False, **kwds):
    '''Get the *materialized dict* or *inline values* tuple.
    '''
    if mdict:
        mdict = _materializedictuple(obj)
    return mdict, kwds


def _repr(obj, clip=80):
    '''Clip long repr() string.
    '''
    try:  # safe repr()
        r = repr(obj).replace(_NL, '\\n')
    except Exception:
        r = 'N/A'
    if len(r) > clip > 0:
        h = (clip // 2) - 2
        if h > 0:
            r = r[:h] + '....' + r[-h:]
    return r


def _SI(size, K=1024, i='i'):
    '''Return size as SI string.
    '''
    if 1 < K <= size:
        f = float(size)
        for si in iter('KMGPTE'):
            f /= K
            if f < K:
                return ' or %.1f %s%sB' % (f, si, i)
    return _NN


def _SI2(size, **kwds):
    '''Return size as regular plus SI string.
    '''
    return str(size) + _SI(size, **kwds)


def _SI3(w, size):
    '''Return size as formatted SI bytes string.
    '''
    return '%*d bytes%s' % (w, size, _SI(size))


# Type-specific referents functions

def _cell_refs(obj, named):
    try:  # handle 'empty' cells
        o = obj.cell_contents
        if named:
            o = _NamedRef('cell_contents', o)
        yield o
    except (AttributeError, ValueError):
        pass


def _class_refs(obj, named):
    '''Return specific referents of a class object.
    '''
    return _refs(obj, named, '__class__', '__doc__', '__mro__', '__name__',
                             '__slots__', '__static_attributes__',
                             '__weakref__', mdict=True)  # __dict__ last


def _co_refs(obj, named):
    '''Return specific referents of a code object.
    '''
    return _refs(obj, named, pref='co_', excl=('co_lnotab',))  # DeprecationWarning


def _dict_refs(obj, named):
    '''Return key and value objects of a dict/proxy.
    '''
    try:
        if named:
            for k, v in _items(obj):
                s  = str(k)
                yield _NamedRef('[K] ' + s, k)
                s += ': ' + _repr(v)
                yield _NamedRef('[V] ' + s, v)
        else:
            for k, v in _items(obj):
                yield k
                yield v
    except (KeyError, ReferenceError, TypeError) as x:
        warn("Iterating '%s': %r" % (_classof(obj), x))


def _enum_refs(obj, named):
    '''Return specific referents of an enumerate object.
    '''
    return _refs(obj, named, '__doc__')


def _exc_refs(obj, named):
    '''Return specific referents of an Exception object.
    '''
    # .message raises DeprecationWarning in CPy 2.6
    return _refs(obj, named, 'args', 'filename', 'lineno', 'msg', 'text')  # , 'message', 'mixed'


def _file_refs(obj, named):
    '''Return specific referents of a file object.
    '''
    return _refs(obj, named, 'mode', 'name')


def _frame_refs(obj, named):
    '''Return specific referents of a frame object.
    '''
    return _refs(obj, named, pref='f_')


def _func_refs(obj, named):
    '''Return specific referents of a function or lambda object.
    '''
    return _refs(obj, named, '__doc__', '__name__', '__code__', '__closure__',
                      pref='func_', excl=('func_globals',))


def _gen_refs(obj, named):
    '''Return the referent(s) of a generator (expression) object.
    '''
    # only some gi_frame attrs, but none of
    # the items to keep the generator intact
    f = getattr(obj, 'gi_frame', None)
    return _refs(f, named, 'f_locals', 'f_code')


def _im_refs(obj, named):
    '''Return specific referents of a method object.
    '''
    return _refs(obj, named, '__doc__', '__name__', '__code__', pref='im_')


def _inst_refs(obj, named):
    '''Return specific referents of a class instance.
    '''
    return _refs(obj, named, '__class__', mdict=True, slots='__slots__')


def _iter_refs(obj, named):
    '''Return the referent(s) of an iterator object.
    '''
    r = gc.get_referents(obj)  # special case
    return _refs(r, named, itor=_nameof(obj) or 'iteref')


def _module_refs(obj, named):
    '''Return specific referents of a module object.
    '''
    n = _nameof(obj) == __name__  # i.e. this module
    # ignore this very module, module is essentially a dict
    return () if n else _dict_refs(obj.__dict__, named)


def _namedtuple_refs(obj, named):
    '''Return specific referents of obj-as-sequence and slots but exclude dict.
    '''
    for r in _refs(obj, named, '__class__', slots='__slots__'):
        yield r
    for r in obj:
        yield r


def _prop_refs(obj, named):
    '''Return specific referents of a property object.
    '''
    return _refs(obj, named, '__doc__', pref='f')


def _seq_refs(obj, unused):  # named unused for PyChecker
    '''Return specific referents of a frozen/set, list, tuple and xrange object.
    '''
    return obj  # XXX for r in obj: yield r


def _stat_refs(obj, named):
    '''Return referents of a os.stat object.
    '''
    return _refs(obj, named, pref='st_')


def _statvfs_refs(obj, named):
    '''Return referents of a os.statvfs object.
    '''
    return _refs(obj, named, pref='f_')


def _tb_refs(obj, named):
    '''Return specific referents of a traceback object.
    '''
    return _refs(obj, named, pref='tb_')


def _type_refs(obj, named):
    '''Return specific referents of a type object.
    '''
    return _refs(obj, named, '__doc__', '__mro__', '__name__',
                             '__slots__', '__weakref__', '__dict__')  # mdict=True


def _weak_refs(obj, unused):  # unused for named
    '''Return weakly referent object.
    '''
    try:  # ignore 'key' of KeyedRef
        yield obj()
    except Exception:  # XXX ReferenceError
        pass


_all_refs = {None, _cell_refs, _class_refs, _co_refs, _dict_refs, _enum_refs,
                   _exc_refs, _file_refs, _frame_refs, _func_refs, _gen_refs,
                   _im_refs, _inst_refs, _iter_refs, _module_refs, _namedtuple_refs,
                   _prop_refs, _seq_refs, _stat_refs, _statvfs_refs, _tb_refs,
                   _type_refs, _weak_refs}  # type: Set[Union[None, Callable], ...]


# Type-specific length functions

def _len(obj):
    '''Safe len().
    '''
    try:
        return len(obj)
    except TypeError:  # no len() nor __len__
        return 0


def _len_array(obj):
    '''Array length (in bytes!).
    '''
    return len(obj) * obj.itemsize


def _len_bytearray(obj):
    '''Bytearray size.
    '''
    return obj.__alloc__()


def _len_code(obj):  # see .../Lib/test/test_sys.py
    '''Length of code object (stack and variables only).
    '''
    return (_len(obj.co_freevars) + obj.co_stacksize +
            _len(obj.co_cellvars) + obj.co_nlocals - 1)


def _len_dict(obj):
    '''Dict length in items (estimate).
    '''
    n = len(obj)  # active items
    if n < 6:  # ma_smalltable ...
        n = 0  # ... in basicsize
    else:  # at least one unused
        n = _power_of_2(n + 1)
    return n


def _len_frame(obj):
    '''Length of a frame object.
    '''
    c = getattr(obj, 'f_code', None)
    return _len_code(c) if c else 0


# _sizeof.Cdigit = sys.int_info.sizeof_digit    # sys.int_info in CPy 3.1+
# _bitsof.Cdigit = sys.int_info.bits_per_digit  # (_sizeof.Cdigit * 15) // 2

# _Typedef(int).base = int.__basicsize__  # == _sizeof.get(0)
# _Typedef(int).item = int.__itemsize__   # == _sizeof.Cdigit

def _len_int(obj):
    '''Length of *int* (multi-precision, formerly long) in Cdigits.
    '''
    n = _sizeof.get(obj, 0) - int.__basicsize__
    return (n // int.__itemsize__) if n > 0 else 0


def _len_iter(obj):
    '''Length (hint) of an iterator.
    '''
    n = getattr(obj, '__length_hint__', None)
    return n() if n and callable(n) else _len(obj)


def _len_list(obj):
    '''Length of list (estimate).
    '''
    n = len(obj)
    # estimate over-allocation
    if n > 8:
        n += 6 + (n >> 3)
    elif n:
        n += 4
    return n


def _len_module(obj):
    '''Module length.
    '''
    return _len(obj.__dict__)  # _len(dir(obj))


def _len_set(obj):
    '''Length of frozen/set (estimate).
    '''
    n = len(obj)
    if n > 8:  # assume half filled
        n = _power_of_2(n + n - 2)
    elif n:  # at least 8
        n = 8
    return n


def _len_slice(obj):
    '''Slice length.
    '''
    try:
        return abs(abs(obj.stop - obj.start) // obj.step)
    except (AttributeError, TypeError, ZeroDivisionError):
        return 0


# REMOVED, see _Slots.__doc__
# def _len_slots(obj):
#     '''Slots length.
#     '''
#     return len(obj) - 1


def _len_struct(obj):
    '''Struct length in bytes.
    '''
    try:
        return obj.size
    except AttributeError:
        return 0


def _len_unicode(obj):
    '''Unicode size.
    '''
    return len(obj) + 1


_all_lens = {None, _len, _len_array, _len_bytearray, _len_code, _len_dict,
                   _len_frame, _len_int, _len_iter, _len_list, _len_module,
                   _len_set, _len_slice, _len_struct, _len_unicode}  # type: Set[Union[None, Callable], ...]


# More private functions and classes

# _old_style = '*'  # marker, OBSOLETE
# _new_style = _NN  # no marker

class _Claskey(object):  # never sized
    '''Wrapper for class objects.
    '''
    # __slots__ = ('_obj',)  # '_sty'

    def __init__(self, obj):
        self._obj = obj  # XXX Weakref.ref(obj)
#       self._sty = _new_style

    def __str__(self):
        r = str(self._obj)
        return (r[:-1] + ' def>') if r.endswith('>') else (r + ' def')

    __repr__ = __str__


# For most objects, the object type is used as the key in the
# _typedefs dict further below, except class and type objects
# instances.  Those are wrapped with separate _Claskey or
# _Instkey instances to be able (1) to distinguish class (and
# type) instances from class (and type) definitions and (2)
# to provide similar results for repr() and str() of classes
# and instances.

_claskeys = {}  # type: Dict[int, _Claskey]


def _claskey(obj):
    '''Wrap a class object.
    '''
    i = id(obj)
    try:
        k = _claskeys[i]
    except KeyError:
        _claskeys[i] = k = _Claskey(obj)
    return k


def _key2tuple(obj):  # PYCHOK expected
    '''Return class and instance keys for a class.
    '''
    t = _typeof(obj) is _Type_type  # isclass(obj):
    return (_claskey(obj), obj) if t else _NoneNone


def _objkey(obj):  # PYCHOK expected
    '''Return the key for any object.
    '''
    k = _typeof(obj)
    if k is _Type_type:  # isclass(obj):
        k = _claskey(obj)
    elif _Udict:
        k = _udictof(k, obj)
    return k


class _NamedRef(object):  # never sized
    '''Store referred object along
       with the name of the referent.
    '''
    # __slots__ = ('name', 'ref')

    def __init__(self, name, ref):
        self.name = name
        self.ref  = ref


class _NamedRefs(list):  # never sized
    '''Container of _NamedRef instances.
    '''
    pass


# class _Slots(tuple):
#     '''Wrapper class for __slots__ attribute at class definition.
#        The instance-specific __slots__ attributes are stored in
#        a "tuple-like" space inside the instance, see Luciano
#        Ramalho, "Fluent Python", page 274+, O'Reilly, 2016 or
#        at <http://Books.Google.com/books>, then search for
#        "Fluent Python" "Space Savings with the __slots__".
#     '''
#     pass


# all kinds of _Typedefs
t =  'static        dynamic        derived        ignored        inferred'
_kind_static, _kind_dynamic, _kind_derived, _kind_ignored, _kind_inferred = \
t = tuple(map(sys.intern, t.split()))  # sys.intern CPy 3+
_all_kinds = set(t)  # type: ignore


class _Typedef(object):  # never sized
    '''Type definition class.
    '''
    base = 0     # basic size in bytes
    both = None  # both data and code if True, code only if False
    inli = None  # has *inline values*
    item = 0     # item size in bytes
    kind = None  # _kind_... value
    leng = None  # _len_...() function or None
    refs = None  # _..._refs() function or None
    type = None  # original type
    vari = None  # item size attr name or _Non_vari
    _get = True  # if False, do NOT use _sizeof.get

    def __init__(self, **kwds):
        self.reset(**kwds)

    def __lt__(self, unused):  # for CPy 3+
        return True

    def __repr__(self):
        return repr(self.args())

    def __str__(self):
        t = [str(self.base), str(self.item)]
        for f in (self.leng, self.refs):
            t.append(_nameof(f) or 'n/a')
        if not self.both:
            t.append('(code only)')
        return ', '.join(t)

    def args(self):  # as args tuple
        '''Return all attributes as arguments tuple.
        '''
        return (self.base, self.item, self.leng, self.refs,
                self.both, self.inli, self.kind, self.type,
                self._get)

    def dup(self, other=None, force=False, **updates):
        '''Duplicate attributes from dict or an other typedef.
        '''
        t = other or _dict_typedef
        d = t.kwds()
        d.update(updates)
        if force:  # set kwds as-is
            self.__dict__.update(d)
        else:
            self.reset(**d)
        return self

    def flat(self, obj, mask=0):
        '''Return the aligned flat size.
        '''
        s = self.base
        if self.inli:
            s += _sizeof.inlined(obj)
        if self.leng and self.item > 0:  # include items
            s += self.leng(obj) * self.item
        # workaround sys.getsizeof bug for _array types
        # (in some Python versions) and for other types
        # with variable .itemsize like numpy.arrays, etc.
        if self._get:
            s = _sizeof.get(obj, s)
        if mask:
            s = _sizeof.align(s, mask)
        return s

    def format(self):
        '''Return format dict.
        '''
        a = _nameof(self.leng)
        return dict(leng=((' (%s)' % (a,)) if a else _NN),
                    item='var' if self.vari else self.item,
                    code=_NN if self.both else ' (code only)',
                    base= self.base, kind= self.kind)

    def kwds(self):
        '''Return all attributes as keywords dict.
        '''
        return dict(base=self.base, both=self.both, item=self.item,
                    inli=self.inli, kind=self.kind, leng=self.leng,
                    refs=self.refs, type=self.type, vari=self.vari,
                    _get=self._get)

    def kwds4(self, obj, **kwds):
        '''Return all attributes for an object as keywords dict.
        '''
        d = self.kwds()  # copy
        if self.leng:
            d.update(len=self.leng(obj))
        if kwds:
            d.update(kwds)
        return d

    def reset(self, base=0,    item=0,    leng=None, refs=None,
                    both=True, inli=None, kind=None, type=None,
                    vari=_Non_vari,       _get=True, **extra):
        '''Reset all specified typedef attributes.
        '''
        if inli is None:
            inli = _TPFLAGS.inlined(type)
        v = vari or _Non_vari
        if v != str(v):  # attr name
            e = dict(vari=v)
        elif base < 0:
            e = dict(base=base)
        elif both not in _Bools:
            e = dict(both=both)
        elif inli not in _Bools:
            e = dict(inli=inli)
        elif item < 0:
            e = dict(item=item)
        elif kind not in _all_kinds:
            e = dict(kind=kind)
        elif leng not in _all_lens:  # XXX or not callable(leng)
            e = dict(leng=leng)
        elif refs not in _all_refs:  # XXX or not callable(refs)
            e = dict(refs=refs)
        elif _get not in _Bools:
            e = dict(_get=_get)
        elif extra:
            e = {}
        else:
            self.base = base
            self.both = both
            self.inli = inli
            self.item = item
            self.kind = kind
            self.leng = leng
            self.refs = refs
            self.type = type  # unchecked, as-is
            self.vari = v
            self._get = _get
            return self
        e.update(extra)
        raise _optionError(self.reset, **e)

    def save(self, t, base=0, heap=False):
        '''Save this typedef plus its class typedef.
        '''
        c, k = _key2tuple(t)
        if k and k not in _typedefs:  # instance key
            _typedefs[k] = self
            if c and c not in _typedefs:  # class key
                b = _basicsize(_typeof(t), base=base, heap=heap)
                k = _kind_ignored if _isignored(t) else self.kind
                _typedefs[c] = _Typedef(base=b, both=False,
                                        kind=k, type=t, refs=_type_refs)
        elif t not in _typedefs:
            if not _isbuiltin2(t):  # array, range, xrange in CPy 2
                s = '%s %s %s' % (self.vari, _moduleof(t), _nameof(t))
                s = '%r %s %s' % ((c, k), self.both, s.strip())
                raise KeyError('typedef %r bad: %s' % (self, s))

            _typedefs[t] = _Typedef(base=_basicsize(t, base=base), both=False,
                                    kind=_kind_ignored, type=t)
        return self

    def set(self, safe_len=False, force=False, **updates):
        '''Set one or more attributes.
        '''
        if force:  # set kwds as-is
            self.__dict__.update(updates)
        elif updates:  # double check
            d = self.kwds()
            d.update(updates)
            self.reset(**d)
        if safe_len and self.item:
            self.leng = _len
        return self


_typedefs = {}  # type: Dict[type, _Typedef]


def _array_kwds(obj):
    # since item size varies by the array data type, set
    # itemsize to 1 byte and use _len_array in bytes;
    # _sizeof.get(array) returns array plus base size
    b = max(56, _sizeof.get(obj, 0) - _len_array(obj))
    return dict(base=b, leng=_len_array, item=_sizeof.Cbyte,
                vari='itemsize',  # array.itemsize
                _get= False)  # no _sizeof.get


def _typedef_both(typ, base=0, item=0, leng=None, refs=None,
                       kind=_kind_static, heap=False, vari=_Non_vari):
    '''Add new typedef for both data and code.
    '''
    v = _Typedef(base=_basicsize(typ, base=base), item=_itemsize(typ, item),
                 refs=refs, leng=leng,
                 both=True, kind=kind, type=typ, vari=vari)
    v.save(typ, base=base, heap=heap)
    return v  # for _dict_typedef


def _typedef_code(typ, base=0, refs=None, kind=_kind_static, heap=False):
    '''Add new typedef for code only.
    '''
    v = _Typedef(base=_basicsize(typ, base=base),  # item=0,
                 refs=refs,
                 both=False, kind=kind, type=typ)
    v.save(typ, base=base, heap=heap)
    return v  # for _dict_typedef


# Static typedefs for data and code types
_typedef_both(complex)
_typedef_both(float)
_typedef_both(int, leng=_len_int)  # see _len_int
_typedef_both(list, refs=_seq_refs, leng=_len_list, item=_sizeof.Cvoidp)  # sizeof(PyObject*)
_typedef_both(property, refs=_prop_refs)
_typedef_both(str, leng=_len_unicode, item=_sizeof.Cunicode)
_typedef_both(_typeof(Ellipsis))
_typedef_both(_typeof(None))

t = _typedef_both(tuple, refs=_seq_refs, leng=_len, item=_sizeof.Cvoidp)  # sizeof(PyObject*)
if _Inline0:
    _typedef_both(_Inline0).dup(t, force=True, base=0, item=0, type=_Inline0, _get=False)  # no _sizeof.get
# _Slots are "tuple-like", REMOVED see _Slots.__doc__
# _typedef_both(_Slots, item=_sizeof.Cvoidp,
#               leng=_len_slots,  # length less one
#               refs=None,  # but no referents
#               heap=True)  # plus head

# dict, mappingproxy, dict_proxy and other dict-like types
_dict_typedef = _typedef_both(dict, item=_sizeof.CPyDictKeyEntry,
                                    leng=_len_dict, refs=_dict_refs)
if _Udict:
    _typedef_both(_Udict).dup(item=_sizeof.CPyDictStrEntry, force=True)
t = _typeof(_Typedef.__dict__)
if t is not dict:  # <class mappingproxy> in CPy 3+?
    _typedef_both(t).dup(force=True)
t = getattr(Types, 'ModuleType', None)
if t:  # <type module> is essentially a dict
    _typedef_both(t).dup(item=_sizeof.CPyModuleObject,
                         leng=_len_module, refs=_module_refs)
# other dict-like classes and types may be derived or inferred,
# provided the module and class name is listed here (see functions
# adict, _isdictype and _infer_dict for further details)
_dict_types = dict(UserDict=('IterableUserDict', 'UserDict'),
                   weakref =('WeakKeyDictionary', 'WeakValueDictionary'))


# Newer or obsolete types
try:  # bool has non-zero __itemsize__ in 3.0
    _typedef_both(bool)
except NameError:  # missing
    pass

try:
    _typedef_both(bytearray, item=_sizeof.Cbyte, leng=_len_bytearray)
except NameError:  # bytearray new in 2.6, 3.0
    pass
try:
    if _typeof(bytes) is not _typeof(str):  # bytes is str in 2.6, bytes new in 2.6, 3.0
        _typedef_both(bytes, item=_sizeof.Cbyte, leng=_len)  # bytes new in 2.6, 3.0
except NameError:  # missing
    pass
# try:  # XXX like bytes
#     _typedef_both(str8, item=_sizeof.Cbyte, leng=_len)  # str8 new in 2.6, 3.0
# except NameError:  # missing
#     pass

try:
    _typedef_both(enumerate, refs=_enum_refs)
except NameError:  # missing
    pass

try:  # Exception is type in CPy 3+
    _typedef_both(Exception, refs=_exc_refs)
except Exception:  # missing
    pass

try:
    _typedef_both(frozenset, item=_sizeof.Csetentry, leng=_len_set, refs=_seq_refs)
except NameError:  # missing
    pass
try:
    _typedef_both(set, item=_sizeof.Csetentry, leng=_len_set, refs=_seq_refs)
except NameError:  # missing
    pass

try:  # not callable()
    _typedef_both(Types.GetSetDescriptorType)
except AttributeError:  # missing
    pass

try:  # not callable()
    _typedef_both(Types.MemberDescriptorType)
except AttributeError:  # missing
    pass

try:
    _typedef_both(_typeof(NotImplemented))  # == Types.NotImplementedType
except NameError:  # missing
    pass

try:  # MCCABE 19
    import numpy as _numpy  # NumPy array, matrix, etc.
    try:
        _numpy_memmap = _numpy.memmap
    except AttributeError:
        _numpy_memmap = None
    try:
        from mmap import PAGESIZE as _PAGESIZE
        if _PAGESIZE < 1024:
            raise ImportError
    except ImportError:
        _PAGESIZE = 4096  # 4 KiB, typical

    def _isnumpy(obj):
        '''Return True for a NumPy arange, array, matrix, memmap, ndarray, etc. instance.
        '''
        try:  # not every numpy obj  hasattr(obj, 'base')
            if hasattr(obj, 'dtype') and hasattr(obj, 'itemsize') \
                                     and hasattr(obj, 'nbytes'):
                return (_moduleof(_classof(obj)).startswith('numpy') or
                        _moduleof(_typeof( obj)).startswith('numpy'))
        except (AttributeError, OSError, ValueError):  # on iOS/Pythonista
            pass
        return False

    def _len_numpy(obj):
        '''NumPy array, matrix, etc. length (in bytes!).
        '''
        return obj.nbytes  # == obj.size * obj.itemsize

    def _len_numpy_memmap(obj):
        '''Approximate NumPy memmap in-memory size (in bytes!).
        '''
        nb = int(obj.nbytes * _sizeof.amapped)
        # round up to multiple of virtual memory page size
        return ((nb + _PAGESIZE - 1) // _PAGESIZE) * _PAGESIZE

    def _numpy_kwds(obj):
        t = _typeof(obj)
        # .nbytes is included in sys.sizeof size for most numpy
        # objects except for numpy.memmap (and for the latter it
        # is the length of the file to be memory-mapped which by
        # default is the file size less the offset specified)
        _i, _v = _sizeof.Cbyte, 'itemsize'
        if t is _numpy_memmap:  # isinstance(obj, _numpy_memmap)
            b, _l, nb = 144, _len_numpy_memmap, 0
        elif t.__name__ in ('str', 'str_'):  # numpy.str Deprecated!
            # make numpy.str_ behave like Python type str
            b  =  81
            _l = _len
            nb = _l(obj)
            _i =  obj.nbytes // nb
            _v = _Non_vari
        else:  # XXX 96, 128, 144 typical?
            b, _l, nb = 96, _len_numpy, obj.nbytes
        # since item size depends on the nympy data type, set
        # itemsize to 1 byte and use _len_numpy in bytes; note,
        # function itemsize returns the actual size in bytes,
        # function leng returns the length in number of items
        return dict(base=max(_sizeof.get(obj, b + nb) - nb, b),
                    item=_i,  # not obj.itemsize!
                    leng=_l,
                    refs=_numpy_refs,
                    vari=_v,  # numpy.itemsize
                    _get= False)  # no _sizeof.get

    def _numpy_refs(obj, named):
        '''Return the .base object for NumPy slices, tile, views, etc.
        '''
        return _refs(obj, named, 'base')

    _all_lens.add(_len_numpy)         # type: ignore
    _all_lens.add(_len_numpy_memmap)  # type: ignore
    _all_refs.add(_numpy_refs)        # type: ignore

except ImportError:  # no NumPy
    _numpy = _numpy_kwds = None  # type: ignore  # see function _typedef below

    def _isnumpy(unused):  # PYCHOK expected
        '''Not applicable, no NumPy.
        '''
        return False

try:
    _typedef_both(range)
except NameError:  # missing
    pass

try:
    _typedef_both(reversed, refs=_enum_refs)
except NameError:  # missing
    pass

try:
    _typedef_both(slice, item=_sizeof.Cvoidp, leng=_len_slice)  # XXX worst-case itemsize?
except NameError:  # missing
    pass

try:
    from os import stat
    _typedef_both(_typeof(stat(curdir)), refs=_stat_refs)  # stat_result
except ImportError:  # missing
    pass

try:
    from os import statvfs
    _typedef_both(_typeof(statvfs(curdir)), refs=_statvfs_refs,  # statvfs_result
                   item=_sizeof.Cvoidp, leng=_len)
except ImportError:  # missing
    pass

try:
    from struct import Struct  # only in CPy 2.5 and 3.0
    _typedef_both(Struct, item=_sizeof.Cbyte, leng=_len_struct)  # len in bytes
except ImportError:  # missing
    pass

try:
    _typedef_both(Types.TracebackType, refs=_tb_refs)
except AttributeError:  # missing
    pass

try:  # <type 'KeyedRef'>
    _typedef_both(Weakref.KeyedRef, refs=_weak_refs, heap=True)  # plus head
except AttributeError:  # missing
    pass

try:  # <type 'weakproxy'>
    _typedef_both(Weakref.ProxyType)
except AttributeError:  # missing
    pass

try:  # <type 'weakref'>
    _typedef_both(Weakref.ReferenceType, refs=_weak_refs)
except AttributeError:  # missing
    pass

# some other, callable types
_typedef_code(object, kind=_kind_ignored)
_typedef_code(super, kind=_kind_ignored)
_typedef_code(_Type_type, kind=_kind_ignored)

try:
    _typedef_code(classmethod, refs=_im_refs)
except NameError:
    pass
try:
    _typedef_code(staticmethod, refs=_im_refs)
except NameError:
    pass
try:
    _typedef_code(Types.MethodType, refs=_im_refs)
except NameError:
    pass

try:  # generator (expression), no itemsize, no len(), not callable()
    _typedef_both(Types.GeneratorType, refs=_gen_refs)
except AttributeError:  # missing
    pass

try:  # <type 'weakcallableproxy'>
    _typedef_code(Weakref.CallableProxyType, refs=_weak_refs)
except AttributeError:  # missing
    pass


def _iter_types(**kwds):  # type-specific iterators
    s = [_items({}), _keys({}), _values({})]
    try:  # reversed list and tuple iterators
        s.extend([reversed([]), reversed(())])
    except NameError:  # missing
        pass

    try:  # callable-iterator
        from re import finditer
        s.append(finditer(_NN, _NN))
        del finditer
    except ImportError:  # missing
        pass

    for t in _values(_typedefs):
        if t.type and t.leng:
            try:  # create an (empty) instance
                s.append(t.type())
            except TypeError:
                pass

    for t in s:
        try:
            t = _typeof(iter(t))
            yield _typedef_both(t, **kwds)
        except (KeyError, TypeError):  # ignore non-iterables, duplicates, etc.
            pass

for t in _iter_types(leng=_len_iter, refs=_iter_refs, item=0):  # PYCHOK no itemsize!
    pass  # _printf('%s: %s', t.type, str(t))
del t, _iter_types


def _typedef(obj, derive=False, frames=False, infer=False):  # MCCABE 22
    '''Create a new typedef for an object.
    '''
    t = _typeof(obj)
    v = _Typedef(base=_basicsize(t, obj=obj),
                 kind=_kind_dynamic, type=t)
#   _printf('new %r %r/%r %s', t, _basicsize(t), _itemsize(t), _repr(dir(obj)))
    if ismodule(obj):  # handle module like dict
        v.dup(item=_sizeof.CPyModuleObject,
              leng=_len_module,
              refs=_module_refs)
    elif _isframe(obj):
        v.set(base=_basicsize(t, base=_sizeof.CPyFrameObject, obj=obj),
              item=_itemsize(t),
              leng=_len_frame,
              refs=_frame_refs)
        if not frames:  # ignore frames
            v.set(kind=_kind_ignored)
    elif iscode(obj):
        v.set(base=_basicsize(t, base=_sizeof.CPyCodeObject, obj=obj),
              item=_sizeof.Cvoidp,
              leng=_len_code,
              refs=_co_refs,
              both=False)  # code only
    elif callable(obj):
        if isclass(obj):  # class or type
            v.set(refs=_class_refs,
                  both=False)  # code only
            if _isignored(obj):
                v.set(kind=_kind_ignored)
        elif isbuiltin(obj):  # function or method
            v.set(both=False,  # code only
                  kind=_kind_ignored)
        elif isfunction(obj):
            v.set(refs=_func_refs,
                  both=False)  # code only
        elif ismethod(obj):
            v.set(refs=_im_refs,
                  both=False)  # code only
        elif isclass(t):  # callable instance, e.g. SCons,
            # handle like any other instance further below
            v.set(item=_itemsize(t), safe_len=True,
                  refs=_inst_refs)  # not code only!
        else:
            v.set(both=False)  # code only
    elif _isdictype(obj) or (infer and _infer_dict(obj)):
        v.dup(kind=_kind_inferred)
    elif _iscell(obj):
        v.set(item=_itemsize(t), refs=_cell_refs)
    elif _isnamedtuple(obj):
        v.set(refs=_namedtuple_refs)
    elif _numpy and _isnumpy(obj):
        v.set(**_numpy_kwds(obj))
    elif isinstance(obj, _array):
        v.set(**_array_kwds(obj))
    elif _isignored(obj) or _isignored(t):
        v.set(kind=_kind_ignored)
    else:  # assume an instance of some class
        if derive:
            p = _derive_typedef(t)
            if p:  # duplicate parent
                v.dup(other=p, kind=_kind_derived)
                return v
        if _issubclass(t, Exception):
            v.set(item=_itemsize(t), safe_len=True,
                  refs=_exc_refs,
                  kind=_kind_derived)
        elif isinstance(obj, Exception):
            v.set(item=_itemsize(t), safe_len=True,
                  refs=_exc_refs)
        else:
            v.set(item=_itemsize(t), safe_len=True,
                  refs=_inst_refs)
    return v


class _Prof(object):  # never sized
    '''Internal type profile class.
    '''
    high   = 0      # largest size
    number = 0      # number of (unique) objects
    objref = None   # largest obj (weakref)
    total  = 0      # total size
    weak   = False  # objref is weakref(obj)

    def __cmp__(self, other):
        if self.total < other.total:
            return -1
        elif self.total > other.total:
            return +1
        elif self.number < other.number:
            return -1
        elif self.number > other.number:
            return +1
        return 0

    def __lt__(self, other):  # for CPy 3+
        return self.__cmp__(other) < 0

    def format(self, clip=0, grand=None):
        '''Return format dict.
        '''
        if self.number > 1:  # avg., plural
            a, p = int(self.total / self.number), 's'
        else:
            a, p = self.total, _NN
        o = self.objref
        if self.weak:
            o = o()
        t = _SI2(self.total)
        if grand:
            t += ' (%s)' % _p100(self.total, grand, prec=0)
        s = _lengstr(o)
        return dict(avg=_SI2(a), high=_SI2(self.high), lengstr=s,
                    obj=_repr(o, clip=clip), plural=p, total=t)

    def update(self, obj, size):
        '''Update this profile.
        '''
        self.number += 1
        self.total += size
        if self.high < size:  # largest
            self.high = size
            try:  # prefer using weak ref
                self.objref, self.weak = Weakref.ref(obj), True
            except TypeError:
                self.objref, self.weak = obj, False


class _Profs(dict):  # never sized
    '''Container of _Prof instances.
    '''
    pass


class _Rank(object):  # never sized
    '''Internal largest object class.
    '''
    deep   = 0      # recursion depth
    id     = 0      # id(obj)
    key    = None   # Typedef
    objref = None   # obj or Weakref.ref(obj)
    pid    = 0      # id(parent obj)
    size   = 0      # size in bytes
    weak   = False  # objref is Weakref.ref

    def __init__(self, key, obj, size, deep, pid):
        self.deep = deep
        self.id = id(obj)
        self.key = key
        try:  # prefer using weak ref
            self.objref, self.weak = Weakref.ref(obj), True
        except TypeError:
            self.objref, self.weak = obj, False
        self.pid = pid
        self.size = size

    def format(self, clip=0, id2x={}):
        '''Return this *rank* as string.
        '''
        def _ix(_id):  # id or parent_id
            return id2x.get(_id, '?')

        o = self.objref() if self.weak else self.objref
        d = (' (at %s)' % (self.deep,)) if self.deep > 0 else _NN
        p = (', pix %s' % (_ix(self.pid),)) if self.pid else _NN
        return '%s: %s%s, ix %s%s%s' % (_prepr(self.key, clip=clip),
               _repr(o, clip=clip), _lengstr(o), _ix(self.id), d, p)


class _Ranks(list):  # never sized
    '''Container of _Rank instances.
    '''
    pass


class _Seen(dict):  # never sized
    '''Internal obj visits counter.
    '''
    def again(self, key):
        try:
            n = self[key] + 1
        except KeyError:
            n = 1
        if n > 0:
            self[key] = n
        return n


# Public classes

class Asized(object):  # never sized
    '''Stores the results of an **asized** object in the following
       5 attributes:

        *size* -- total size of the object (including referents)

        *flat* -- flat size of the object (in bytes)

        *name* -- name or ``repr`` of the object

        *refs* -- tuple containing an **Asized** instance for each referent

        *tobj* -- the object or its type.
    '''
    # __slots__ = ('flat', 'name', 'refs', 'size', 'tobj')
    refs = ()  # empty, _NamedRefs()

    def __init__(self, size, flat, refs=None, name=None, tobj=None):
        self.size = size  # total size
        self.flat = flat  # flat size
        self.refs = tuple(refs) if refs else Asized.refs  # and isinstance(refs, _NamedRefs)
        self.name = name  # name, repr or None
        self.tobj = tobj if tobj is None else _typeof(tobj)

    def __str__(self):
        s = 'size %r, flat %r, refs[%d]' % (self.size, self.flat, len(self.refs))
        if self.name:
            s += ', name %r' % (self.name,)
        if self.tobj:
            s += ', type %s' % (_repr(self.tobj),)
        return s

    def format(self, format='%(name)s size=%(size)d flat=%(flat)d',
                     depth=-1, order_by='size', indent=_NN):
        '''Format the size information of the object and of all
           sized referents as a string.

            *format* -- Specifies the format per instance (with 'name',
                        'size' and 'flat' as interpolation parameters)

            *depth* -- Recursion level up to which the referents are
                       printed (use -1 for unlimited)

            *order_by* -- Control sort order of referents, valid choices
                          are 'name', 'size' and 'flat'

            *indent* -- Optional indentation (default '')
        '''
        t = indent + (format % dict(size=self.size, flat=self.flat,
                                    name=self.name))
        if depth and self.refs:
            rs = sorted(self.refs, key=lambda r: getattr(r, order_by),
                                   reverse=order_by in ('size', 'flat'))
            rs = [r.format(format=format, depth=depth-1, order_by=order_by,
                           indent=indent+'    ') for r in rs]
            t = _NL.join([t] + rs)
        return t

    def get(self, name, dflt=None):
        '''Return the named referent (or *dflt* if not found).
        '''
        for ref in self.refs:
            if name == ref.name:
                return ref
        return dflt


class Asizer(object):  # never sized
    '''Sizer state and options to accumulate sizes.
    '''
    _above_  = 1024  # rank only objs of size 1K+
    _align_  = 8     # alignment, power-of-2
    _clip_   = 80
    _code_   = False
    _cutoff_ = 0  # in percent
    _derive_ = False
    _detail_ = 0  # for Asized only
    _frames_ = False
    _infer_  = False
    _limit_  = 100
    _stats_  = 0

    _debugs  = 0  # see ._clear, _reset, ._sizer
    _depth   = 0  # deepest recursion
    _excl_d  = None  # {}
    _ign_d   = _kind_ignored
    _mask    = 7   # see _align_
    _missed  = 0   # due to errors
    _profile = False  # no profiling
    _profs   = None   # _Profs()
    _ranked  = 0
    _ranks   = []     # type: List[_Ranks] # sorted by decreasing size
    _seen    = None   # _Seen()
    _stream  = None   # I/O stream for printing
    _total   = 0      # total size

    def __init__(self, **opts):
        '''New **Asizer** accumulator.

           See this module documentation for more details.
           See method **reset** for all available options and defaults.
        '''
        self._excl_d = {}
        self.reset(**opts)

    def _c100(self, stats):
        '''Cutoff as percentage (for backward compatibility)
        '''
        s = int(stats)
        c = int((stats - s) * 100.0 + 0.5) or self.cutoff
        return s, c

    def _clear(self):
        '''Clear state.
        '''
        self._depth = 0   # recursion depth reached
        self._missed = 0   # due to errors
        self._profile = False
        self._profs = _Profs()
        self._ranked = 0
        self._ranks = _Ranks()
        self._seen = _Seen()
        self._total = 0   # total size
        for k in _keys(self._excl_d):
            self._excl_d[k] = 0
        # don't size, profile or rank private, possibly large objs
        m = sys.modules[__name__]
        self.exclude_objs(self, self._excl_d, m, m.__dict__, m.__doc__,
                                self._profs, self._ranks, self._seen,
                               _typedefs)

    @property_RO
    def _incl_d(self):
        '''Return "incl. (byte)code" or "".
        '''
        return ' (incl. code)' if self.code else _NN

    def _nameof(self, obj, _attr=_NN):
        '''Return the object's name.
        '''
        return _nameof(obj, _NN) or _attr or self._repr(obj)

    def _prepr(self, obj):
        '''Like **prepr()**.
        '''
        return _prepr(obj, clip=self._clip_)

    def _printd(self, d, i, **kwds):
        '''Print a *_debugsizer* step.
        '''
        d  =  max(0, d)
        n  =  self._seen.get(i, 0)
        t  = _kwdstr(deep=d, seen=n, **kwds).replace('function ', _NN)
        d *= ' '  # indentation
        self._printf(' %s%+d id=%#x, %s', d, self._debugs, i, t)
        self._debugs += 1

    def _printf(self, fmt, *args, **print3options):
        '''Print to sys.stdout or the configured stream if any is
           specified and if the file keyword argument is not already
           set in the **print3options** for this specific call.
        '''
        if self._stream and not print3options.get('file', None):
            print3options = dict(file=self._stream, **print3options)
        _printf(fmt, *args, **print3options)

    def _printo(self, w, num, adj, **print3options):
        '''Print an *objects* summary stat.
        '''
        s = _plural(num)
        self._printf('%*d object%s %s', w, num, s, adj, **print3options)

    def _prof(self, key):
        '''Get _Prof object.
        '''
        try:
            p = self._profs[key]
        except KeyError:
            self._profs[key] = p = _Prof()
            # self.exclude_objs(p)  # superfluous
        return p

    def _rank(self, key, obj, size, deep, pid):
        '''Rank 100 largest objects by size.
        '''
        rs = self._ranks
        # bisect, see <http://GitHub.com/python/cpython/blob/master/Lib/bisect.py>
        i, j = 0, len(rs)
        while i < j:
            m = (i + j) // 2
            if size < rs[m].size:
                i = m + 1
            else:
                j = m
        if i < 100:
            r = _Rank(key, obj, size, deep, pid)
            rs.insert(i, r)
            # self.exclude_objs(r)  # superfluous
            while len(rs) > 100:
                rs.pop()
            # self._ranks[:] = rs[:100]
        self._ranked += 1

    def _repr(self, obj):
        '''Like ``repr()``.
        '''
        return _repr(obj, clip=self._clip_)

    def _sizer(self, obj, pid, deep, sized, **_attr):  # MCCABE 18
        '''Size an object, recursively.
        '''
        s, f, i = 0, 0, id(obj)
        # _Inline0 instances are re-used and the same id()
        # may be seen again containing different items
        if _typeof(obj) is _Inline0:  # skip self._seen
            deep -= 1  # ignore the _Inline0 depth
#           sized = None  # accumulate sizes only
        elif i not in self._seen:
            self._seen[i] = 1
        elif deep or self._seen[i]:
            # skip obj if seen before
            # or if ref of a given obj
            self._seen.again(i)  # type: int
            if self._debugs:
                self._printd(deep, i, type=_typeof(obj), **_attr)
            if sized:
                s = sized(s, f, name=self._nameof(obj), tobj=obj)
                self.exclude_objs(s)
            return s  # zero
        else:  # deep == seen[i] == 0
            self._seen.again(i)  # type: int
        try:
            k, rs = _objkey(obj), None
            if k in self._excl_d:
                self._excl_d[k] += 1
            else:
                v = _typedefs.get(k, None)
                if not v:  # new typedef
                    _typedefs[k] = v = _typedef(obj, derive=self._derive_,
                                                     frames=self._frames_,
                                                      infer=self._infer_)
                if (v.both or self._code_) and v.kind is not self._ign_d:
                    s = f = v.flat(obj, self._mask)  # flat size
                    if self._debugs:
                        self._printd(deep, i, flat=s, **v.kwds4(obj, **_attr))
                    if self._profile and v.type is not _Inline0:
                        # profile based on *flat* size
                        self._prof(k).update(obj, s)
                    # recurse to refs, but not for nested modules
                    if v.refs and  deep < self._limit_ and \
                              not (deep and ismodule(obj)):
                        s, rs = self._sizerefs2(obj, i, deep, sized, s, rs, v)
                if self._stats_ and s > self._above_ > 0:
                    # rank based on *total* size
                    self._rank(k, obj, s, deep, pid)
        except RuntimeError:  # XXX RecursionLimitExceeded:
            self._missed += 1
        if self._debugs and s != f != 0:
            self._printd(deep, i, size=s, **v.kwds4(obj, **_attr))
        if not deep:
            self._total += s  # accumulate
        if sized:
            s = sized(s, f, name=self._nameof(obj, **_attr), refs=rs, tobj=obj)
            self.exclude_objs(s)  # if _typeof(s).__module__ is not __name__
        return s

    def _sizerefs2(self, obj, pid, deep, sized, s, rs, v):
        '''Size the referents of an object.
        '''
        z, d = self._sizer, (deep + 1)
        if sized and deep < self._detail_:
            # use named referents
            rs = _NamedRefs()
            for o in v.refs(obj, True):
                if isinstance(o, _NamedRef):
                    r = z(o.ref, pid, d, sized, _attr=o.name)
                    r.name = o.name
                else:
                    r = z(o, pid, d, sized)
                    r.name = self._nameof(o)
                rs.append(r)
                s += r.size
        elif self._debugs:
            for o in v.refs(obj, True):
                if isinstance(o, _NamedRef):
                    s += z(o.ref, pid, d, None, _attr=o.name)
                else:
                    s += z(o, pid, d, None)
        else:  # just size and accumulate
            for o in v.refs(obj, False):
                s += z(o, pid, d, None)  # , sized?
        # deepest recursion reached
        if self._depth < d:
            self._depth = d
        return s, rs

    def _sizes(self, objs, sized):
        '''Yield the size or **Asized** for each given object.
        '''
        if objs:
            s = {}
            self.exclude_objs(s)
            self.exclude_refs(*objs)  # skip refs to objs

            for o in objs:
                i = id(o)
                if i in s:
                    self._seen.again(i)
                else:
                    s[i] = self._sizer(o, 0, 0, sized)
                yield s[i]

    @property_RO
    def above(self):
        '''Get the large object size threshold (int).
        '''
        return self._above_

    @property_RO
    def align(self):
        '''Get the size alignment (int).
        '''
        return self._align_

    def asized(self, *objs, **opts):
        '''Return a tuple with an **Asized** instance for each given
           object with size information and referents up to the given
           detaillevel (and with modified options, see method **set**).

           If only one *objs* is given, only **Asized** instance for
           that object is returned.

           Duplicate *objs* will have the same **Asized** instance,
           ignored *objs* will have an **Asized** instance with
           size zero.
        '''
        if opts:
            self.set(**opts)
        t = tuple(self._sizes(objs, Asized))
        return t if len(t) != 1 else t[0]

    def asizeof(self, *objs, **opts):
        '''Return the combined size of the given objects
           (with modified options, see method **set**).
        '''
        if opts:
            self.set(**opts)
        self.exclude_refs(*objs)  # skip refs to objs
        return sum(self._sizer(o, 0, 0, None) for o in objs)

    def asizesof(self, *objs, **opts):
        '''Return the size of each given object (with modified
           options, see method  **set**).

           Duplicate *objs* will have the same size (instance),
           ignored *objs* will have size zero.
        '''
        if opts:
            self.set(**opts)
        return tuple(self._sizes(objs, None))

    @property_RO
    def clip(self):
        '''Get the clipped string length (int).
        '''
        return self._clip_

    @property_RO
    def code(self):
        '''Size the (byte) code (bool).
        '''
        return self._code_

    @property_RO
    def cutoff(self):
        '''Stats cutoff (int).
        '''
        return self._cutoff_

    @property_RO
    def derive(self):
        '''Derive types (bool).
        '''
        return self._derive_

    @property_RO
    def detail(self):
        '''Get the detail level for **Asized** refs (int).
        '''
        return self._detail_

    @property_RO
    def duplicate(self):
        '''Get the number of duplicate objects seen so far (int).
        '''
        return sum(1 for v in _values(self._seen) if v > 1)  # == len

    def exclude_objs(self, *objs):
        '''Exclude the specified objects from sizing, profiling and ranking.
        '''
        for o in objs:
            self._seen.setdefault(id(o), -1)

    def exclude_refs(self, *objs):
        '''Exclude any references to the specified objects from sizing.

           While any references to the given objects are excluded, the
           objects will be sized if specified as positional arguments
           in subsequent calls to methods **asizeof** and **asizesof**.
        '''
        for o in objs:
            self._seen.setdefault(id(o), 0)

    def exclude_types(self, *objs):
        '''Exclude the specified object instances and types from sizing.

           All instances and types of the given objects are excluded,
           even objects specified as positional arguments in subsequent
           calls to methods **asizeof** and **asizesof**.
        '''
        for o in objs:
            for t in _key2tuple(o):
                if t and t not in self._excl_d:
                    self._excl_d[t] = 0

    @property_RO
    def excluded(self):
        '''Get the types being excluded (tuple).
        '''
        return tuple(_keys(self._excl_d))

    @property_RO
    def frames(self):
        '''Ignore stack frames (bool).
        '''
        return self._frames_

    @property_RO
    def ignored(self):
        '''Ignore certain types (bool).
        '''
        return bool(self._ign_d)

    @property_RO
    def infer(self):
        '''Infer types (bool).
        '''
        return self._infer_

    @property_RO
    def limit(self):
        '''Get the recursion limit (int).
        '''
        return self._limit_

    @property_RO
    def missed(self):
        '''Get the number of objects missed due to errors (int).
        '''
        return self._missed

    def print_largest(self, w=0, cutoff=0, **print3options):
        '''Print the largest objects.

           The available options and defaults are:

            *w=0*           -- indentation for each line

            *cutoff=100*    -- number of largest objects to print

            *print3options* -- some keyword arguments, like Python 3+ print
        '''
        c = int(cutoff) if cutoff else self._cutoff_
        n = min(len(self._ranks), max(c, 0))
        s = self._above_
        if n > 0 and s > 0:
            self._printf('%s%*d largest object%s (of %d over %s)', _NL, w, n,
                        _plural(n), self._ranked, _SI3(0, s), **print3options)
            id2x = dict((r.id, i) for i, r in enumerate(self._ranks))
            for r in self._ranks[:n]:
                t = r.format(self._clip_, id2x)
                self._printf('%s: %s', _SI3(w, r.size), t, **print3options)

    def print_profiles(self, w=0, cutoff=0, **print3options):
        '''Print the profiles above *cutoff* percentage.

           The available options and defaults are:

                *w=0*           -- indentation for each line

                *cutoff=0*      -- minimum percentage printed

                *print3options* -- some keyword arguments, like Python 3+ print
        '''
        z = len(self._profs)
        # get the profiles with non-zero size or count
        t = [(v, k) for k, v in _items(self._profs) if v.total > 0 or v.number > 1]
        if (z - len(t)) < 9:  # just show all
            t = [(v, k) for k, v in _items(self._profs)]
        if t:
            if self._total:
                c = int(cutoff) if cutoff else self._cutoff_
                C = int(c * 0.01 * self._total)
                s = ' (% of grand total)'
            else:
                C = c = 0
                s = _NN
            r = len(t)
            self._printf('%s%*d profile%s:  total%s, average, and largest flat size%s:  largest object',
                         _NL, w, r, _plural(r), s, self._incl_d, **print3options)
            f = 'object%(plural)s:  %(total)s, %(avg)s, %(high)s:  %(obj)s%(lengstr)s'
            t = [(v, self._prepr(k)) for v, k in t]  # replace types with str for CPy 3.11+
            for v, k in sorted(t, reverse=True):
                s = f % v.format(self._clip_, self._total)
                self._printf('%*d %s %s', w, v.number, k, s, **print3options)
                r -= 1
                if r > 1 and v.total < C:
                    self._printf('%+*d profiles below cutoff (%.0f%%)', w, r, c)
                    break
            z -= len(t)
            if z > 0:
                self._printf('%+*d %r object%s', w, z, 'zero', _plural(z), **print3options)

    def print_stats(self, objs=(), opts={}, sized=(), sizes=(), stats=3, **print3options):
        '''Prints the statistics.

           The available options and defaults are:

                *w=0*           -- indentation for each line

                *objs=()*       -- optional, list of objects

                *opts={}*       -- optional, dict of options used

                *sized=()*      -- optional, tuple of **Asized** instances returned

                *sizes=()*      -- optional, tuple of sizes returned

                *stats=3*       -- print stats, see function **asizeof**

                *print3options* -- some keyword arguments, like Python 3+ print
        '''
        s = min(opts.get('stats', stats) or 0, self.stats)
        if s > 0:  # print stats
            w = len(str(self.missed + self.seen + self.total)) + 1
            t = c = _NN
            o = _kwdstr(**opts)
            if o and objs:
                c = ', '
            # print header line(s)
            if sized and objs:
                n = len(objs)
                if n > 1:
                    self._printf('%sasized(...%s%s) ...', _NL, c, o, **print3options)
                    for i in range(n):  # no enumerate in CPy 2.2.3
                        self._printf('%*d: %s', w - 1, i, sized[i], **print3options)
                else:
                    self._printf('%sasized(%s): %s', _NL, o, sized, **print3options)
            elif sizes and objs:
                self._printf('%sasizesof(...%s%s) ...', _NL, c, o, **print3options)
                for z, o in zip(sizes, objs):
                    self._printf('%s%s:  %s', _SI3(w, z), self._incl_d, self._repr(o), **print3options)
            else:
                if objs:
                    t = self._repr(objs)
                self._printf('%sasizeof(%s%s%s) ...', _NL, t, c, o, **print3options)
            # print summary
            self.print_summary(w=w, objs=objs, **print3options)
            # for backward compatibility, cutoff from fractional stats
            s, c = self._c100(s)
            self.print_largest(w=w, cutoff=c if s < 2 else 10, **print3options)
            if s > 1:  # print profile
                self.print_profiles(w=w, cutoff=c, **print3options)
                if s > 2:  # print typedefs
                    self.print_typedefs(w=w, **print3options)  # PYCHOK .print_largest?

    def print_summary(self, w=0, objs=(), **print3options):
        '''Print the summary statistics.

           The available options and defaults are:

                *w=0*           -- indentation for each line

                *objs=()*       -- optional, list of objects

                *print3options* -- some keyword arguments, like Python 3+ print
        '''
        self._printf('%s%s', _SI3(w, self._total), self._incl_d, **print3options)
        if self._mask:
            self._printf('%*d byte aligned', w, self._mask + 1, **print3options)
        self._printf('%*d byte sizeof(void*)', w, _sizeof.Cvoidp, **print3options)
        self._printo(w, len(objs or ()), 'given', **print3options)
        self._printo(w, self.sized, 'sized', **print3options)
        if self._excl_d:
            n = sum(_values(self._excl_d))
            self._printo(w, n, 'excluded', **print3options)
        self._printo(w, self.seen, 'seen', **print3options)
        self._printo(w, self.ranked, 'ranked', **print3options)
        self._printo(w, self.missed, 'missed', **print3options)
        n = self.duplicate
        self._printf('%*d duplicate%s', w, n, _plural(n), **print3options)
        if self._depth > 0:
            self._printf('%*d deepest recursion', w, self._depth, **print3options)

    def print_typedefs(self, w=0, **print3options):
        '''Print the types and dict tables.

           The available options and defaults are:

                *w=0*           -- indentation for each line

                *print3options* -- some keyword arguments, like Python 3+ print
        '''
        for k in sorted(_all_kinds):
            # XXX CPy 3+ doesn't sort type objects
            c = self._code_
            t = [(self._prepr(a), v) for a, v in _items(_typedefs)
                                              if v.kind == k and (v.both or c)]
            if t:
                self._printf('%s%*d %s type%s:  basicsize, itemsize, _len_(), _refs()',
                             _NL, w, len(t), k, _plural(len(t)), **print3options)
                for a, v in sorted(t):
                    self._printf('%*s %s:  %s', w, _NN, a, v, **print3options)
        # dict and dict-like classes
        t = sum(len(v) for v in _values(_dict_types))
        if t:
            self._printf('%s%*d dict/-like classes:', _NL, w, t, **print3options)
            for m, v in _items(_dict_types):
                self._printf('%*s %s:  %s', w, _NN, m, self._prepr(v), **print3options)

    @property_RO
    def ranked(self):
        '''Get the number of objects ranked by size so far (int).
        '''
        return self._ranked

    def reset(self, above=1024, align=8, clip=80, code=False,  # PYCHOK too many args
                    cutoff=10, derive=False, detail=0, frames=False, ignored=True,
                    infer=False, limit=100, stats=0, stream=None, **extras):
        '''Reset sizing options, state, etc. to defaults.

           The available options and default values are:

                *above=0*      -- threshold for largest objects stats

                *align=8*      -- size alignment

                *code=False*   -- incl. (byte)code size

                *cutoff=10*    -- limit large objects or profiles stats

                *derive=False* -- derive from super type

                *detail=0*     -- **Asized** refs level

                *frames=False* -- ignore frame objects

                *ignored=True* -- ignore certain types

                *infer=False*  -- try to infer types

                *limit=100*    -- recursion limit

                *stats=0*      -- print statistics, see function **asizeof**

                *stream=None*  -- output stream for printing

           See function **asizeof** for a description of the options.
        '''
        self._above_ = above
        self._align_ = align
        self._clip_ = clip
        self._code_ = code
        self._cutoff_ = cutoff
        self._derive_ = derive
        self._detail_ = detail  # for Asized only
        self._frames_ = frames
        self._infer_ = infer
        self._limit_ = limit
        self._stats_ = stats
        self._stream = stream
        self._ign_d = _kind_ignored if ignored else None
        # clear state
        self._clear()
        self.set(align=align, code=code, cutoff=cutoff, stats=stats)
        if extras:
            try:  # *_debugsizer=False* -- print ._sizer steps
                d = extras.pop('_debugsizer')
                self._debugs = 1 if d else 0
            except KeyError:
                pass
            if extras:
                raise _optionError(self.reset, Error=KeyError, **extras)

    @property_RO
    def seen(self):
        '''Get the number objects seen so far (int).
        '''
        return sum(v for v in _values(self._seen) if v > 0)

    def set(self, above=None, align=None, code=None, cutoff=None,
                  frames=None, detail=None, limit=None, stats=None):
        '''Set some sizing options.  See also **reset**.

           The available options are:

                *above*  -- threshold for largest objects stats

                *align*  -- size alignment

                *code*   -- incl. (byte)code size

                *cutoff* -- limit large objects or profiles stats

                *detail* -- **Asized** refs level

                *frames* -- size or ignore frame objects

                *limit*  -- recursion limit

                *stats*  -- print statistics, see function **asizeof**

           Any options not set remain unchanged from the previous setting.
        '''
        # adjust
        if above is not None:
            self._above_ = int(above)
        if align is not None:
            self._align_ =  align
            self._mask   = _sizeof.mask(align)
        if code is not None:
            self._code_ = code
        if detail is not None:
            self._detail_ = detail
        if frames is not None:
            self._frames_ = frames
        if limit is not None:
            self._limit_ = limit
        if stats is not None:
            if stats < 0:
                raise _optionError(self.set, stats=stats)
            # for backward compatibility, cutoff from fractional stats
            s, c = self._c100(stats)
            self._cutoff_ = int(cutoff) if cutoff else c
            self._stats_ = s
            self._profile = s > 1  # profile types

    @property_RO
    def sized(self):
        '''Get the number objects sized so far (int).
        '''
        return sum(1 for v in _values(self._seen) if v > 0)

    @property_RO
    def stats(self):
        '''Get the stats and cutoff setting (float).
        '''
        return self._stats_  # + (self._cutoff_ * 0.01)

    @property_RO
    def total(self):
        '''Get the total size (in bytes) accumulated so far.
        '''
        return self._total

_asizer = Asizer()  # PYCHOK singleton


# Public functions

def adict(*classes):
    '''Install one or more classes to be handled as *dict*.

       By default, *type(os.environ)* is installed as *adict*.
    '''
    a = True
    for c in classes:
        # if class is dict-like, add class
        # name to _dict_types[_moduleof(c)]
        n = _nameof(c)
        if n and isclass(c) and _infer_dict(c):
            m = _moduleof(c)
            t = _dict_types.get(m, ())
            if n not in t:  # extend tuple
                _dict_types[m] = t + (n,)
        else:  # not a dict-like class
            a = False
    return a  # all installed if True


assert adict(_typeof(environ))  # _Environ
del environ


def amapped(percentage=None):
    '''Set/get approximate mapped memory usage as a percentage
       of the mapped file size.

       Sets the new percentage if not None and returns the
       previously set percentage.

       Applies only to *numpy.memmap* objects.
    '''
    p = _sizeof.amapped * 100.0
    if percentage is not None:
        _sizeof.amapped = max(0, min(1, percentage / 100.0))
    return p


def asized(*objs, **opts):
    '''Return a tuple containing an **Asized** instance for each
       object passed as positional argument.

       The available options and defaults are:

            *above=0*      -- threshold for largest objects stats

            *align=8*      -- size alignment

            *code=False*   -- incl. (byte)code size

            *cutoff=10*    -- limit large objects or profiles stats

            *derive=False* -- derive from super type

            *detail=0*     -- Asized refs level

            *frames=False* -- ignore stack frame objects

            *ignored=True* -- ignore certain types

            *infer=False*  -- try to infer types

            *limit=100*    -- recursion limit

            *stats=0*      -- print statistics

       If only one object is given, the return value is the **Asized**
       instance for that object.  Otherwise, the length of the returned
       tuple matches the number of given objects.

       The **Asized** size of duplicate and ignored objects will be zero.

       Set *detail* to the desired referents level and *limit* to the
       maximum recursion depth.

       See function **asizeof** for descriptions of the other options.
    '''
    _asizer.reset(**opts)
    if objs:
        t = _asizer.asized(*objs)
        _asizer.print_stats(objs, opts=opts, sized=t)  # show opts as _kwdstr
        _asizer._clear()
    else:
        t = ()
    return t


def asizeof(*objs, **opts):
    '''Return the combined size (in bytes) of all objects passed
       as positional arguments.

       The available options and defaults are:

            *above=0*      -- threshold for largest objects stats

            *align=8*      -- size alignment

            *clip=80*      -- clip ``repr()`` strings

            *code=False*   -- incl. (byte)code size

            *cutoff=10*    -- limit large objects or profiles stats

            *derive=False* -- derive from super type

            *frames=False* -- ignore stack frame objects

            *ignored=True* -- ignore certain types

            *infer=False*  -- try to infer types

            *limit=100*    -- recursion limit

            *stats=0*      -- print statistics

       Set *align* to a power of 2 to align sizes.  Any value less
       than 2 avoids size alignment.

       If *all* is True and if no positional arguments are supplied.
       size all current gc objects, including module, global and stack
       frame objects.

       A positive *clip* value truncates all repr() strings to at
       most *clip* characters.

       The (byte)code size of callable objects like functions,
       methods, classes, etc. is included only if *code* is True.

       If *derive* is True, new types are handled like an existing
       (super) type provided there is one and only of those.

       By default certain base types like object, super, etc. are
       ignored.  Set *ignored* to False to include those.

       If *infer* is True, new types are inferred from attributes
       (only implemented for dict types on callable attributes
       as get, has_key, items, keys and values).

       Set *limit* to a positive value to accumulate the sizes of
       the referents of each object, recursively up to the limit.
       Using *limit=0* returns the sum of the flat sizes of the
       given objects.  High *limit* values may cause runtime errors
       and miss objects for sizing.

       A positive value for *stats* prints up to 9 statistics, (1)
       a summary of the number of objects sized and seen and a list
       of the largests objects with size over *above* bytes, (2) a
       simple profile of the sized objects by type and (3+) up to 6
       tables showing the static, dynamic, derived, ignored, inferred
       and dict types used, found respectively installed.
       The fractional part of the *stats* value (x 100) is the number
       of largest objects shown for (*stats*1.+) or the cutoff
       percentage for simple profiles for (*stats*=2.+).  For example,
       *stats=1.10* shows the summary and the 10 largest objects,
       also the default.

       See this module documentation for the definition of flat size.
    '''
    t, p, x = _objs_opts_x(asizeof, objs, **opts)
    _asizer.reset(**p)
    if t:
        if x:  # don't size, profile or rank gc.get_objects container
            _asizer.exclude_objs(t)
        s = _asizer.asizeof(*t)
        _asizer.print_stats(objs=t, opts=opts)  # show opts as _kwdstr
        _asizer._clear()
    else:
        s = 0
    return s


def asizesof(*objs, **opts):
    '''Return a tuple containing the size (in bytes) of all objects
       passed as positional arguments.

       The available options and defaults are:

            *above=1024*   -- threshold for largest objects stats

            *align=8*      -- size alignment

            *clip=80*      -- clip ``repr()`` strings

            *code=False*   -- incl. (byte)code size

            *cutoff=10*    -- limit large objects or profiles stats

            *derive=False* -- derive from super type

            *frames=False* -- ignore stack frame objects

            *ignored=True* -- ignore certain types

            *infer=False*  -- try to infer types

            *limit=100*    -- recursion limit

            *stats=0*      -- print statistics

       See function **asizeof** for a description of the options.

       The length of the returned tuple equals the number of given
       objects.

       The size of duplicate and ignored objects will be zero.
    '''
    _asizer.reset(**opts)
    if objs:
        t = _asizer.asizesof(*objs)
        _asizer.print_stats(objs, opts=opts, sizes=t)  # show opts as _kwdstr
        _asizer._clear()
    else:
        t = ()
    return t


def _typedefof(obj, save=False, **opts):
    '''Get the typedef for an object.
    '''
    k = _objkey(obj)
    v = _typedefs.get(k, None)
    if not v:  # new typedef
        v = _typedef(obj, **opts)
        if save:
            _typedefs[k] = v
    return v


def basicsize(obj, **opts):
    '''Return the basic size of an object (in bytes).

       The available options and defaults are:

           *derive=False* -- derive type from super type

           *infer=False*  -- try to infer types

           *save=False*   -- save the object's type definition if new

       See this module documentation for the definition of *basic size*.
    '''
    b = t = _typedefof(obj, **opts)
    if t:
        b = t.base
    return b


def flatsize(obj, align=0, **opts):
    '''Return the flat size of an object (in bytes), optionally aligned
       to the given power-of-2.

       See function **basicsize** for a description of other available options.

       See this module documentation for the definition of *flat size*.
    '''
    f = t = _typedefof(obj, **opts)
    if t:
        m = _sizeof.mask(align) if align else 0
        f =  t.flat(obj, mask=m)
    return f


def itemsize(obj, **opts):
    '''Return the item size of an object (in bytes).

       See function **basicsize** for a description of the available options.

       See this module documentation for the definition of *item size*.
    '''
    i = t = _typedefof(obj, **opts)
    if t:
        i, v = t.item, t.vari
        if v and i == _sizeof.Cbyte:
            i = getattr(obj, v, i)
    return i


def leng(obj, **opts):
    '''Return the length of an object, in number of *items*.

       See function **basicsize** for a description of the available options.
    '''
    n = t = _typedefof(obj, **opts)
    if t:
        n = t.leng
        if n and callable(n):
            i, v, n = t.item, t.vari, n(obj)
            if v and i == _sizeof.Cbyte:
                i = getattr(obj, v, i)
                if i > _sizeof.Cbyte:
                    n = n // i
    return n


def named_refs(obj, **opts):
    '''DEPRECATED on 2025.07.11, use function **refs(obj, named=True, ...)**.'''
    return list(refs(obj, named=True, **opts))


def refs(obj, named=False, **opts):
    '''Yield the *referents* of an object, each a single ref or a 2-tuple
       (name, ref) if **named=True*.

       See function **basicsize** for a description of the available options.
    '''
    v = _typedefof(obj, **opts)
    if v:
        v = v.refs
        if v and callable(v):
            for r in v(obj, named):
                if named:
                    try:
                        r = (r.name, r.ref)
                    except AttributeError:
                        continue
                yield r


__all__ += tuple(map(_nameof, (Asized, Asizer,  # classes
                               adict, amapped, asized, asizeof, asizesof,
                               basicsize, flatsize, itemsize, leng, refs)))

if __name__ == '__main__':  # MCCABE 15

    def _main(args):

        def _gc_collect():
            if '-gc' in args:
                _printf(' gc.collect(): %d', gc.collect())

        def _examples(**kwds):
            '''*_Typedef* and size some examples.
            '''
            t = 2**99, _array('B', range(127)), _array('d', range(100))
            if _numpy:
                t += (_numpy.arange(0),
                      _numpy.array(range(0)),
                      _numpy.ma.masked_array([]),
                      _numpy.memmap(sys.executable, mode='r'),  # dtype=_numpy.uint8
                      _numpy.float64(0),
                      _numpy.ndarray(0),
                      _numpy.uint64(2**63)),
                try:  # .matrix deprecated in numpy 1.19.3
                    t += _numpy.matrix(range(0)),
                except AttributeError:
                    pass
            if _Inline0:
                t += _Inline0(),
            if _Udict:
                t += _Udict(),
            asizesof(*t, **kwds)  # sizing creates _Typedefs dynamically
            return t

        if '-examples' in args or '-x' in args:
            # show some asizeof examples
            _gc_collect()

            _ = _examples(above=0, cutoff=0, stats=2)
            amapped(100)  # numpy.memmap'd file size
            # print summary + 10 largest
            asizeof(all=True, stats=9, above=1024, frames='-frames' in sys.argv)

            _gc_collect()

        elif '-types' in args or '-t' in args:
            # show static and some dynamic _typedefs
            if '-debugsizer' in args:
                _asizer._debugs = 1
            _ = _examples(stats=0)
            n =  len(_typedefs)
            w =  len(str(n)) * ' '
            _printf('%s%d type definitions: %s and %s, kind ... %s', _NL,
                     n, 'basic-', 'itemsize (leng)', '-type[def]s')
            for k, td in sorted((_prepr(k), td) for k, td in _items(_typedefs)):
                t = '%(base)s and %(item)s%(leng)s, %(kind)s%(code)s' % td.format()
                _printf('%s %s: %s', w, k, t)

        else:  # if '-version' in sys.argv or '-v' in sys.argv
            import platform as p
            a = p.architecture()[0]
            m = p.machine()
            v = sys.version.split()[0]
            p = 'Python %s %s %s %s' % (v, a, m, sys.platform)  # p.system()
            if _numpy:
                p = '%s, %s %s' % (p, _nameof(_numpy), _numpy.__version__)
            t = dict(inlined=_inlined(_sizeof))
            t.update(_sizeof.__dict__)  # materialized
            t = _kwdstr(**t).replace(', C', ', .C')
            _printf('%s %s (%s) _sizeof.%s', __file__, __version__, p, t)

    _main(sys.argv[1:])

# License from the initial version of this source file follows:

# --------------------------------------------------------------------
# Copyright 2002-2025 ProphICy Semiconductor, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# - Neither the name of ProphICy Semiconductor, Inc. nor the names
#   of its contributors may be used to endorse or promote products
#   derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
# --------------------------------------------------------------------
