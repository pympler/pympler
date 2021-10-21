.. _classtracker:

========================
Tracking class instances
========================

Introduction
------------

.. automodule:: pympler.classtracker
   :noindex:

Usage
-----

Let's start with a simple example. Suppose you have this module::

    >>> class Employee:
    ...    pass
    ...    
    >>> class Factory:
    ...    pass
    ...
    >>> def create_factory():
    ...    factory = Factory()
    ...    factory.name = "Assembly Line Unlimited"
    ...    factory.employees = []
    ...    return factory
    ...
    >>> def populate_factory(factory):
    ...    for x in xrange(1000):
    ...        worker = Employee()
    ...        worker.assigned = factory.name
    ...        factory.employees.append(worker)
    ...
    >>> factory = create_factory()
    >>> populate_factory(factory)

The basic tools of the `ClassTracker` are tracking objects or classes, taking
snapshots, and printing or dumping statistics. The first step is to decide what
to track. Then spots of interest for snapshot creation have to be identified.
Finally, the gathered data can be printed or saved::
    
    >>> factory = create_factory()
    >>> from pympler.classtracker import ClassTracker
    >>> tracker = ClassTracker()
    >>> tracker.track_object(factory)
    >>> tracker.track_class(Employee)
    >>> tracker.create_snapshot()
    >>> populate_factory(factory)
    >>> tracker.create_snapshot()
    >>> tracker.stats.print_summary()
    ---- SUMMARY ------------------------------------------------------------------
                                             active      1.22 MB      average   pct
      Factory                                     1    344     B    344     B    0%
      __main__.Employee                           0      0     B      0     B    0%
                                             active      1.42 MB      average   pct
      Factory                                     1      4.75 KB      4.75 KB    0%
      __main__.Employee                        1000    195.38 KB    200     B   13%
    -------------------------------------------------------------------------------


Basic Functionality
-------------------

Instance Tracking
~~~~~~~~~~~~~~~~~

The purpose of instance tracking is to observe the size and lifetime of an
object of interest. Creation and destruction timestamps are recorded and the
size of the object is sampled when taking a snapshot.

To track the size of an individual object::
    
    from pympler.classtracker import ClassTracker
    tracker = ClassTracker()
    obj = MyClass()
    tracker.track_object(obj)

Class Tracking
~~~~~~~~~~~~~~

Most of the time it's cumbersome to track individual instances
manually. Instead, all instances of a class can automatically be tracked with
*track_class*::

    tracker.track_class(MyClass)

All instances of `MyClass` (or a class that inherits from `MyClass`) created
hereafter are tracked.

Tracked Object Snapshot
~~~~~~~~~~~~~~~~~~~~~~~

Tracking alone will not reveal the size of an object. The idea of the
`ClassTracker` is to sample the sizes of all tracked objects at configurable
instants in time. The `create_snapshot` function computes the size of all
tracked objects::

    tracker.create_snapshot('Before juggling with tracked objects')
    ...
    tracker.create_snapshot('Juggling aftermath')

With this information, the distribution of the allocated memory can be
apportioned to tracked classes and instances.

Print Statistics
~~~~~~~~~~~~~~~~

The gathered data can be investigated with `print_stats`. This prints all
available data. To filter and limit the output the more powerful "Off-line
analysis" API can be used instead.

Advanced Functionality
----------------------

Per-referent Sizing
~~~~~~~~~~~~~~~~~~~

It may not be enough to know the total memory consumption of an object.
Detailed per-referent statistics can be gathered recursively up to a given
resolution level. Resolution level 1 means that all direct referents of an
object will be sized. Level 2 also include the referents of the direct
referents, and so forth. Note that the member variables of an instance are
typically stored in a dictionary and are therefore second order referents. ::

    tracker.track_object(obj, resolution_level=2)

The resolution level can be changed if the object is already tracked::

    tracker.track_change(obj, resolution_level=2)

The new setting will become effective for the next snapshot. This can help to
raise the level of detail for a specific instance of a tracked class without
logging all the class' instances with a high verbosity level. Nevertheless, the
resolution level can also be set for all instances of a class::

    tracker.track_class(MyClass, resolution_level=1)

.. warning::

    Please note the per-referent sizing is very memory and computationally
    intensive. The recorded meta-data must be stored for each referent of a tracked
    object which might easily quadruplicate the memory footprint of the build.
    Handle with care and don't use too high resolution levels, especially if set
    via `track_class`.

Instantiation traces
~~~~~~~~~~~~~~~~~~~~

Sometimes it is not trivial to observe where an object was instantiated. The
`ClassTracker` can record the instantiation stack trace for later evaluation. ::

    tracker.track_class(MyClass, trace=1)

This only works with tracked classes, and **not** with individual objects.

Background Monitoring
~~~~~~~~~~~~~~~~~~~~~

The `ClassTracker` can be configured to take periodic snapshots automatically. The
following example will take 10 snapshots a second (approximately) until the
program has exited or the periodic snapshots are stopped with
`stop_periodic_snapshots`. Background monitoring also works if no object is
tracked. In this mode, the `ClassTracker` will only record the total virtual
memory associated with the program. This can be useful in combination with
background monitoring to detect memory usage which is transient or not
associated with any tracked object. ::

    tracker.start_periodic_snapshots(interval=0.1)

.. warning::

    Take care if you use automatic snapshots with tracked objects. The sizing
    of individual objects might be inconsistent when memory is allocated or freed
    while the snapshot is being taken.

Off-line Analysis
~~~~~~~~~~~~~~~~~

The more data is gathered by the `ClassTracker` the more noise is produced on the
console. The acquired `ClassTracker` log data can also be saved to a file for
off-line analysis::

    tracker.stats.dump_stats('profile.dat')

The `Stats` class of the `ClassTracker` provides means to evaluate the collected
data. The API is inspired by the `Stats class
<http://docs.python.org/lib/profile-stats.html>`_ of the Python profiler. It is
possible to sort the data based on user preferences, filter by class and limit
the output noise to a manageable magnitude. 

The following example reads the dumped data and prints the ten largest Node
objects to the standard output::

    from pympler.classtracker_stats import ConsoleStats

    stats = ConsoleStats()
    stats.load_stats('profile.dat')
    stats.sort_stats('size').print_stats(limit=10, clsname='Node')

HTML Statistics
~~~~~~~~~~~~~~~

The `ClassTracker` data can also be emitted in HTML format together with a
number of charts (needs python-matplotlib). HTML statistics can be emitted
using the *HtmlStats* class::

    from pympler.classtracker_stats import HtmlStats
    HtmlStats(tracker=tracker).create_html('profile.html')

However, you can also reprocess a previously generated dump::

    from pympler.classtracker_stats import HtmlStats

    stats = HtmlStats(filename='profile.dat')
    stats.create_html('profile.html')

Limitations and Corner Cases
----------------------------

Inheritance
~~~~~~~~~~~

Class tracking allows to observe multiple classes that might have an
inheritance relationship. An object is only tracked once. The tracking
parameters of the most specialized tracked class control the actual tracking of
an instance.

Shared Data
~~~~~~~~~~~

Data shared between multiple tracked objects won't lead to overestimations.
Shared data will be assigned to the first (evaluated) tracked object it is
referenced from, but is only counted once. Tracked objects are evaluated in the
order they were announced to the `ClassTracker`. This should make the assignment
deterministic from one run to the next, but has two known problems. If the
`ClassTracker` is used concurrently from multiple threads, the announcement order
will likely change and may lead to random assignment of shared data to
different objects. Shared data might also be assigned to different objects
during its lifetime, see the following example::

    class A():
      pass

    from pympler.classtracker import ClassTracker
    tracker = ClassTracker()

    a = A()
    tracker.track_object(a)
    b = A()
    tracker.track_object(b)
    b.content = range(100000)
    tracker.create_snapshot('#1')
    a.notmine = b.content
    tracker.create_snapshot('#2')

In the snapshot #1, *b*'s size will include the size of the large list. Then
the list is shared with *a*. The snapshot *#2* will assign the list's footprint
to *a* because it was registered before *b*.

If a tracked object *A* is referenced from another tracked object *B*,
*A*'s size is not added to *B*'s size, regardless of the order in which they
are sized.

Accuracy
~~~~~~~~

`ClassTracker` uses the `sizer` module to gather size informations. Asizeof makes
assumptions about the memory footprint of the various data types. As it is
implemented in pure Python, there is no way to know how the actual Python
implementation allocates data and lays it out in memory. Thus, the size numbers
are not really accurate and there will always be a divergence between the
virtual size of the Python process as reported by the OS and the sizes asizeof
estimates.

Most recent C/Python versions contain a `facility to report accurate size
informations <http://bugs.python.org/issue2898>`_ of Python objects. If available,
asizeof uses it to improve the accuracy.

Morphing objects
~~~~~~~~~~~~~~~~

Some programs instate the (anti-)pattern of changing an instance' class at runtime, for
example to morph abstract objects into specific derivations during runtime. The
pattern looks like the following in the code::

    obj.__class__ = OtherClass

If the instance which is morphed is already tracked, the instance will continue
to be tracked by the `ClassTracker`. If the target class is tracked but the
instance is not, the instance will only be tracked if the constructor of the
target class is called as part of the morphing process. The object will not be
re-registered to the new class in the tracked object index. However, the new
class is stored in the representation of the object as soon as the object is
sized.

