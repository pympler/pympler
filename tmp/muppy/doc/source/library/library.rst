.. _library:

=======
Library
=======

Muppy works with the `sys.getsizeof` (see sys_) function which was added in
Python 2.6. It is possible to use muppy with Python versions prior to 2.6. In
this case, :ref:`asizeof <asizeof>` is used to compute the size of an object.

Some functions of the library work on the entire object set of your running
Python application. Expect some time-intensive computations.

It was also considered to make use of the weak reference feature (see weakref_)
available in Python. But since it is not possible to use weak refs on many types
of objects (e.g. lists and dicts) it was decided to not further pursue this approach.

The muppy package provides a set of modules. Functions from the muppy module are
available through the package itself as well as further convenience functions. 

Modules
-----------

.. toctree::
   :maxdepth: 1

   muppy
   refbrowser
   refbrowser-gui
   summary
   tracker


.. _sys: http://docs.python.org/dev/library/sys.html
.. _weakref: http://docs.python.org/lib/module-weakref.html
