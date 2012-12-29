.. _related_work:

============
Related Work
============

Pympler is a merger of several approaches toward memory profiling of Python
applications. This page lists other known tools. If you know yet another one or
find the description is not correct you can create a new issue at
http://code.google.com/p/pympler/issues.

asizeof
-------

Asizeof is a pure-Python module to estimate the size of objects by Jean
Brouwers. This implementation has been published previously on
aspn.activestate.com. It is possible to determine the size of an
object and its referents recursively up to a specified level. asizeof is also
distributed with muppy and allows the usage of muppy with Python versions prior
to Python 2.6.

asizeof has become a part of Pympler.

URL: http://code.activestate.com/recipes/546530/

Heapmonitor
-----------

"The Heapmonitor is a facility delivering insight into the memory distribution
of SCons. It provides facilities to size individual objects and can track all
objects of certain classes." It was developed in 2008 by Ludwig Haehne.

URL: http://www.scons.org/wiki/LudwigHaehne/HeapMonitor

Heapmonitor has become a part of Pympler.

Heapy
-----

Heapy was part of the Master thesis by Sverker Nilsson done in 2006. It is part
of the umbrella project guppy. Heapy has a very mathematical approach as it
works in terms of sets, partitions, and equivalence relations.  It allows to
gather information about objects at any given time, but only objects starting
from a specific root object. Type information for standard objects is supported
by default and type information for non-standard object types can be
added through an interface.

URL: http://guppy-pe.sourceforge.net

Meliae
------

"This project is similar to heapy (in the 'guppy' project), in its attempt to
understand how memory has been allocated.

Currently, its main difference is that it splits the task of computing summary
statistics, etc of memory consumption from the actual scanning of memory
consumption. It does this, because I often want to figure out what is going on
in my process, while my process is consuming huge amounts of memory (1GB, etc).
It also allows dramatically simplifying the scanner, as I don't allocate python
objects while trying to analyze python object memory consumption."

Meliae is being developed by John A Meinel since 2009. It is well suited for
offline analysis of full memory dumps.

URL: https://launchpad.net/meliae

muppy
-----
"Muppy [..] enables the tracking of memory usage during runtime and the
identification of objects which are leaking. Additionally, tools are provided
which allow to locate the source of not released objects." It was developed in
2008 by Robert Schuppenies. 

muppy has become a part of Pympler.

Python Memory Validator
-----------------------

A commercial Python memory validator which uses the Python Reflection
API.

URL: http://www.softwareverify.com/python/memory/index.html

PySizer
-------

PySizer was a Google Summer of Code 2005 project by Nick Smallbone. It relies on
the garbage collector to gather information about existing objects. The
developer can create a summary of the current set of objects and then analyze the
extracted data. It is possible to group objects by criteria like object type and
apply filtering mechanisms to the sets of objects.  Using a patched CPython
version it is also possible to find out where in the code a certain object was
created. Nick points out that "the interface is quite sparse, and some things
are clunky". The project is deprecated and the last supported Python version is
2.4.

URL: http://pysizer.8325.org/

Support Tracking Low-Level Memory Usage in CPython
--------------------------------------------------

This is an experimental implementation of CPython-level memory tracking by Brett
Cannon. Done in 2006, it tackles the problem at the core,
the CPython interpreter itself. To trace the memory usage he suggests to tag
every memory allocation and de-allocation. All actions involving memory take a
`const char *` argument that specifies what the memory is meant
for. Thus every allocation and freeing of memory is
explicitly registered. On the Python level the total memory usage as well as "a
dict with keys as the string names of the types being tracked and values of the
amount of memory being used by the type" are available.

URL: http://svn.python.org/projects/python/branches/bcannon-sandboxing/PEP.txt

