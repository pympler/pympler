.. _remarks:

===========================
Remarks on Memory Profiling
===========================

Memory profiling of Python applications can take place at different levels and
have various goals. For example, you experience a consumption of memory which is
more what you would have expected and now you are interested in where your memory
goes. Or you experience an increase of memory usage over the runtime of your
application, which is a strong indicator that the program leaks memory.

Muppy's focus is on the latter, the identification of memory leaks.

Quoting Wikipedia (memory_leak_), a memory leak is a ::

  "[..] particular type of unintentional memory consumption by a computer
  program where the program fails to release memory when no longer needed. This
  condition is normally the result of a bug in a program that prevents it from
  freeing up memory that it no longer needs."

Only Python
-----------
  
Memory profiling of Python applications can take place on several levels.  For
one, the Python code itself can be the cause for a problem. But also other
possibilities should be considered. Python itself is written in C, Java, or
possibly C# (even more are possible). Also, modules used may be written in C
(c_api_) or make use of third party software (tkinter_). Thus, an unusual memory
consumption may also be caused by non-Python code.

Muppy only considers Python code. You will not be able to identify leaks caused
by non-Python code with muppy.

Observer Effect
---------------

When profiling an application you will experience the observer_effect_. You
therefore have to take some precautions. For example, calling

.. code-block:: python

   import muppy
   all_objects = muppy.get_objects()

will give you all existing objects which can be reached directly or indirectly
through the garbage collector. The problem is though, all objects now are
referenced by one more instance: *all_objects*. Why is this a problem? Because
objects which may have been collected by the garbage collector (see
garbage_collection_), will now be spared. The next time you have a look at all
existing objects, the same you have seen at the first time will be there, plus
some more. But this does not proof a memory leak in your application, only a bad
approach for monitoring that app.

To deal with this problem you can use the :mod:`summary` module. Often it is
sufficient to work with aggregated data instead of handling the entire set of
existing objects. You can recognize a memory leak based only on the number and
size of existing objects, you don't need every single leaking object for this.

Garbage Collection
------------------

If you analyze the state of objects, be aware of the Python garbage collector
(GC) and how it works. First of all, only container objects are handled by the
GC. A container object is an object which holds references to other objects. A
tuple is a container object, an integer is not. Although you may delete all your
references to a container object, it does not mean that all existing references
are deleted. For example, an object A is referencing another object B which also
holds a reference to A. This means the object will not be deleted. At least not
until the garbage collector is invoked, because the GC is able to detect and
resolve cyclic references. But normally a GC run is not predictable. Thus, it is
likely that when analyzing objects, you also get a bunch of 'old' objects (that
is objects which shouldn't be there anymore) in your result set. Therefore muppy
will invoke `gc.collect()` before gathering information about the current object
state.


.. _c_api: http://docs.python.org/api/api.html
.. _garbage_collection: http://diveintopython.org/object_oriented_framework/instantiating_classes.html#d0e12165  
.. _observer_effect: http://en.wikipedia.org/wiki/Observer_effect
.. _memory_leak: http://en.wikipedia.org/w/index.php?title=Memory_leak&oldid=227879672
.. _tkinter: http://docs.python.org/lib/module-Tkinter.html
