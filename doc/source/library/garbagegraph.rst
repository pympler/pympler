.. _garbage:
   
====================
pympler.garbagegraph
====================

Garbage occurs if objects refer too each other in a circular fashion. Such
reference cycles cannot be freed automatically and must be collected by the
garbage collector. While it is sometimes hard to avoid creating reference
cycles, preventing such cycles saves garbage collection time and limits the
lifetime of objects. Moreover, some objects cannot be collected by the garbage
collector.

Reference cycles can be visualized with the help of 
`graphviz <http://www.graphviz.org>`_.

.. automodule:: pympler.garbagegraph

Classes
-------

.. autoclass:: GarbageGraph

   .. automethod:: __init__

   .. automethod:: render

   .. automethod:: split

   .. automethod:: write_graph

   .. automethod:: print_stats

Functions
---------

.. autofunction:: start_debug_garbage

.. autofunction:: end_debug_garbage
