Pympler is a development tool to measure, monitor and analyze the
memory behavior of Python objects in a running Python application.

By pympling a Python application, detailed insight in the size and
the lifetime of Python objects can be obtained.  Undesirable or
unexpected runtime behavior like memory bloat and other "pymples"
can easily be identified.

Pympler integrates 3 previously separate modules into a single,
comprehensive profiling tool.  The :ref:`asizeof <asizeof>` module
provides basic size information for one or several Python objects,
module :ref:`muppy <muppy>` is used for on-line monitoring of a Python
application and module :ref:`heapmonitor <heapmonitor>` provides
off-line analysis of the lifetime of selected Python objects.

Pympler is written entirely in Python, with no dependencies to
external libraries or projects. Both the :ref:`heapmonitor
<heapmonitor>` and the :ref:`muppy <muppy>` module will work with
Python 2.4, 2.5, and 2.6. The :ref:`asizeof <asizeof>` module has
been tested with Python 2.2.3, 2.3.7, 2.4.5, 2.5.1, 2.5.2, 2.6 or
3.0rc1 on CentOS 4.6, SuSE 9.3, MacOS X 10.4.11 Tiger (Intel) and
Panther 10.3.9 (PPC), Solaris 10 and Windows XP all 32-bit Python
and on RHEL 3u7 and Solaris 10 both 64-bit Python.


Target Audience
---------------

Every Python developer interested in analyzing the memory consumption
of his or her Python program should find a suitable, readily usable
facility in Pympler.


Usage Examples
--------------

Aaron is curious how much memory certain Python objects consume.  He
uses one of the :ref:`asizeof <asizeof>` functions to get the size of
these objects and all associated referents.

Peter is trying to compare different implementations of a new parser
module.  For each implementation, he uses the :ref:`asizeof <asizeof>`
module to print simple statistics like size and number of objects
summarized by type.

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
the :ref:`heapmonitor <heapmonitor>` to track and profile her
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

