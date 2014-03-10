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
`Highcharts <http://www.highcharts.com>`_. Pympler has been tested with
Python 2.5, 2.6, 2.7, 3.1, 3.2 and 3.3.

Pympler is platform independent and has been tested on various Linux
distributions (32bit and 64bit), Windows XP, Windows 7 and MacOS X.


Download
--------

If you have *pip* installed, the easiest way to get Pympler is::

    pip install pympler

Alternately, download Pympler releases from the `Python Package Index
<https://pypi.python.org/pypi/Pympler>`_ or `check out the latest
development revision
<https://github.com/pympler/pympler>`_ with git. Please
see the README file for installation instructions.


Target Audience
---------------

Every Python developer interested in analyzing the memory consumption
of his or her Python program should find a suitable, readily usable
facility in Pympler.


Usage Examples
--------------

``pympler.asizeof`` can be used to investigate how much memory certain Python
objects consume. You can use one of the :ref:`asizeof <asizeof>` functions to
get the size of these objects and all associated referents::

    >>> from pympler import asizeof
    >>> obj = [1, 2, (3, 4), 'text']
    >>> asizeof.asizeof(obj)
    176
    >>> print asizeof.asized(obj, detail=1).format()
    [1, 2, (3, 4), 'text'] size=176 flat=48
        (3, 4) size=64 flat=32
        'text' size=32 flat=32
        1 size=16 flat=16
        2 size=16 flat=16

Graham has been notified that his Python script leaks memory. Looking at
the garbage collector debug output does not reveal where the leaks come
from.  Thus he decides to use the :ref:`muppy <muppy>` module to see which actions
result in an increased memory usage.  Graham discovers that whenever
his script iterates over the input set, a new dict object is created.
With the help of the `muppy` module he can identify where these new
dicts are referenced and eliminates the leak. 

Helen maintains a complex application that is taking up a large amount
of memory.  She would like to reduce the memory footprint of her
program by optimizing or restructuring her code.  She has a number of
optimization candidates and she would like to know if optimizing one
of them would likely reduce the total memory footprint.  Helen uses
the :ref:`Class Tracker <classtracker>` to track and profile her
candidate classes.  The results tell her which class instances take up
the largest shares of memory and are therefore best suited for
optimization attempts.  After trying to optimize her code she runs the
program again and compares the profiling results to quantify the
improvements.


History
-------

Pympler was founded in August 2008 by Jean Brouwers, Ludwig Haehne,
and Robert Schuppenies with the goal of providing a complete and
stand-alone memory profiling solution for Python.


