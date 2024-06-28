Pympler is a development tool to measure, monitor and analyze the
memory behavior of Python objects in a running Python application.

By pympling a Python application, detailed insight in the size and
the lifetime of Python objects can be obtained.  Undesirable or
unexpected runtime behavior like memory bloat and other "pymples"
can easily be identified.

Pympler integrates three previously separate modules into a single,
comprehensive profiling tool.  The :ref:`asizeof <asizeof>` module
provides basic size information for one or several Python objects,
module :ref:`muppy <muppy>` is used for on-line monitoring of a Python
application and module :ref:`Class Tracker <classtracker>` provides
off-line analysis of the lifetime of selected Python objects. 

A web profiling frontend exposes process statistics, garbage
visualisation and class tracker statistics.


Requirements
------------

Pympler is written entirely in Python, with no dependencies to external
libraries. It integrates `Bottle <http://bottlepy.org>`_ and
`Flot <http://www.flotcharts.org>`_. Pympler has been tested with
Python 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11 and 3.12.

Pympler is platform independent and has been tested on various Linux
distributions,Windows and MacOS.


Download
--------

If you have *pip* installed, the easiest way to get Pympler is::

    pip install pympler

Alternately, download Pympler releases from the `Python Package Index
<https://pypi.org/project/Pympler>`_ or `check out the latest development
revision <https://github.com/pympler/pympler>`_ with git. Please see the README
file for installation instructions.


Target Audience
---------------

Every Python developer interested in analyzing the memory consumption
of their Python program should find a suitable, readily usable
facility in Pympler.


Usage Examples
--------------

``pympler.asizeof`` can be used to investigate how much memory certain Python
objects consume. In contrast to ``sys.getsizeof``, ``asizeof`` sizes objects
recursively. You can use one of the :ref:`asizeof <asizeof>` functions to get
the size of these objects and all associated referents::

    >>> from pympler import asizeof
    >>> obj = [1, 2, (3, 4), 'text']
    >>> asizeof.asizeof(obj)
    176
    >>> print(asizeof.asized(obj, detail=1).format())
    [1, 2, (3, 4), 'text'] size=176 flat=48
        (3, 4) size=64 flat=32
        'text' size=32 flat=32
        1 size=16 flat=16
        2 size=16 flat=16

Memory leaks can be detected by using :ref:`muppy <muppy>`. While the garbage
collector debug output can report circular references this does not easily
reveal where the leaks come from. Muppy can identify if objects are leaked out
of a scope between two reference points::

    >>> from pympler import tracker
    >>> tr = tracker.SummaryTracker()
    >>> function_without_side_effects()
    >>> tr.print_diff()
      types |   # objects |   total size
    ======= | =========== | ============
       dict |           1 |    280     B
       list |           1 |    192     B

Tracking the lifetime of objects of certain classes can be achieved with the
:ref:`Class Tracker <classtracker>`. This gives insight into instantiation
patterns and helps to understand how specific objects contribute to the memory
footprint over time::

   >>> from pympler import classtracker
   >>> tr = classtracker.ClassTracker()
   >>> tr.track_class(Document)
   >>> tr.create_snapshot()
   >>> create_documents()
   >>> tr.create_snapshot()
   >>> tr.stats.print_summary()
                 active      1.42 MB      average   pct
      Document     1000    195.38 KB    200     B   13%


History
-------

Pympler was founded in August 2008 by Jean Brouwers, Ludwig Haehne,
and Robert Schuppenies with the goal of providing a complete and
stand-alone memory profiling solution for Python.
