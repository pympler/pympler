.. _muppy_tutorial:

==================================
Tutorial - Track Down Memory Leaks
==================================

This tutorial shows you ways in which :term:`muppy` can be used to track down
memory leaks. From my experience, this can be done in 3 steps, each answering
a different question.

#. Is there a leak?
#. What objects leak?
#. Where does it leak?

IDLE
====
My first real-life test for :term:`muppy` was IDLE_, which is "the Python
IDE built with the Tkinter GUI toolkit." It offers the following features:

- coded in 100% pure Python, using the Tkinter GUI toolkit
- cross-platform: works on Windows and Unix (on Mac OS, there are currently
  problems with Tcl/Tk) 
- multi-window text editor with multiple undo, Python colorizing and many other
  features, e.g. smart indent and call tips 
- Python shell window (a.k.a. interactive interpreter)
- debugger (not complete, but you can set breakpoints, view and step)

Because it is integrated in every Python distribution, runs locally and provides
easy interactive feedback, it was a nice first candidate to test the tools of muppy.

The task was to check if IDLE leaks memory, if so, what objects are leaking, and
finally, why are they leaking.

Preparations
------------
IDLE is part of every Python distribution and can be found at
:file:`Lib/idlelib`. The modified version which makes use of muppy can be found
at http://code.google.com/p/muppy/source/browse/trunk#trunk/playground/idlelib.

With IDLE having a GUI, I also wanted to be able to interact with muppy through
the GUI. This can be done in :file:`Lib/idlelib/Bindings.py` and
:file:`Lib/idlelib/PyShell.py`. For details, please refer to the modified
version mentioned above. 

Task 1: Is there a leak?
------------------------
At first, we need to find out if there are any objects leaking at all. We will
have a look at the objects, invoke an action, and look at the objects again. 

.. code-block:: python

   from pympler import tracker

   self.memory_tracker = tracker.SummaryTracker()
   self.memory_tracker.print_diff()

The last step is repeated after each invocation. Let's start with something
simple which should not leak. We will check the Windows resize. You can invoke
it in the menu at `Windows->Zoom Height`.

At first call `print_diff` till it has calibrated. That is, the first one or two
times, you will get some output because there is still something going on in the
background. But then you should get this::

  types |   # objects |   total size
  ====== | =========== | ============
  
Which means nothing has changed since the last invocation of `print_diff`. Now
let's call `Windows->Zoom Height` and invoke `print_diff` again.::

               types |   # objects |   total size
  ================== | =========== | ============
                dict |           1 |     280    B
                list |           1 |     176    B
    _sre.SRE_Pattern |           1 |      88    B
               tuple |           1 |      80    B
                 str |           0 |       7    B

Seems as this requires some of the above mentioned objects. Let's repeat it.::

   types |   # objects |   total size
  ====== | =========== | ============
  
Okay, nothing changed, so nothing is leaking. But we see that often, the first
call to a function creates some objects, which then exist on a second
invocation.

Next, we try something different. We will open a new window. Let's have a look
at the Path Browser at `File->Path Browser`.::

                                                  types |   # objects |   total size
  ===================================================== | =========== | ============
                                                   dict |          18 |     14.26 KB
                                                  tuple |         146 |     13.17 KB
                                                   list |           2 |     11.67 KB
                                                    str |          97 |      7.85 KB
                                                   code |          46 |      5.52 KB
                                               function |          45 |      5.40 KB
                                               classobj |           9 |    864     B
                     instancemethod (<function wakeup>) |           3 |    240     B
                   instancemethod (<function __call__>) |           3 |    240     B
                  instance(<class Tkinter.CallWrapper>) |           3 |    216     B
                                                 module |           3 |    168     B
    instance(<class idlelib.WindowList.ListedToplevel>) |           1 |     72     B

Let's repeat it.::

                                                  types |   # objects |   total size
  ===================================================== | =========== | ============
                                                   dict |           5 |      2.17 KB
                                                   list |           0 |    384     B
                                                    str |           5 |    259     B
                     instancemethod (<function wakeup>) |           3 |    240     B
                   instancemethod (<function __call__>) |           3 |    240     B
                  instance(<class Tkinter.CallWrapper>) |           3 |    216     B
    instance(<class idlelib.WindowList.ListedToplevel>) |           1 |     72     B

Mh, still some new objects. Repeating this procedure several times will reveal
that here indeed we have a leak.

Task 2: What objects leak?
--------------------------
So let's have a closer look at the diff. We see 5 new `dicts` and `strings`, a
bit more memory usage by `lists`, 3 `wakeup` and `__call__` instance methods, 3
`CallWrapper` and 1 `ListedToplevel`. We know the standard types, but the last
couple of objects seem to be from IDLE. 

We ignore the standard type objects for now. It is more likely that these are
only children of some other instances which are causing the leak.

We start with the `ListedTopLevel` object. One invocation of `File->Path
Browser` and one more of this type looks like this object is not garbage
collected, although it should have been. Searching for `ListedTopLevel` in
`idlelib/` reveals that is the base class to all window objects of IDLE. We can
assume that opening the Path Browser, a new window object is created, but
closing the window does not remove the reference.

Next, we take a look at the `wakeup` instance method of which we have three more
on each invocation. Searching the code, we find it to be defined in
`idlelib/WindowList.py`. This piece of code is used to give users of IDLE a list
of currently open windows. Every time a new window is created, it will be added
to the `Windows` menu, from where the user can select any open window. `wakeup`
is the method which will bring the selected window up front. Adding a window
calls menu.add_command, linking menu and the wakeup command together.

.. _menu_add_command:
.. code-block:: python

   menu.add_command(label=title, command=window.wakeup)

So we are getting closer. Only `__call__` and `Tkinter.CallWrapper` are left. As
the name indicates, the latter is located in the Tkinter module, which is part
of the standard library of Python. So let's dive into it. The CallWrapper
docstring states::

  Internal class. Stores function to call when some user defined Tcl function is
  called e.g. after an event occurred.

Also, CallWrapper contains a method called `__call__`, which is used to invoke
the stored function call. A CallWrapper is created by the method `_register`
which then creates a command (Tk speak) and adds it's name to a list called
`self._tclCommands`.

So what do we know so far? Every time a Path Browser is opened, a window is
created, but not deleted when closed again. It has something to do with the
`wakeup` method of the window. This method is wrapped as a Tcl command and then
linked to the window list menu. Also, we have traced this wrapping back to
Tkinter library, where names of the function wrappers are stored in an attribute
called `_tclCommands`.

This brings us to the third question. 

Task 3: Where is the leak?
--------------------------
`_tclCommands` stores the names of all commands linked to a widget. The base
class for interior widgets (of which the menu is one), has a method called
`destroy` which::

	  Delete all Tcl commands created for this widget in the Tcl
	  interpreter.

as well as a method `deletecommand` which deletes a single Tcl command. Both
remove commands as by there name. Among them, we find our CallWrappers'
`__call__` used to wrap the wakeup of the Path Browser window.

So we should expect at least either one to be invoked when a window is closed
(best would be the invocation of only deletecommand). This would also go in line
with `menu.add_command` we identified :ref:`above<menu_add_command>`. And
indeed, in `idlelib/EditorWindow.py`, `menu.delete` is called. So where is the
problem?

We return to `Tkinter.py` and have a closer look at `delete` method::

    def delete(self, index1, index2=None):
        """Delete menu items between INDEX1 and INDEX2 (not included)."""
        self.tk.call(self._w, 'delete', index1, index2)

Mh, it looks like the menu item is deleted, but what about the attached
command? Let's ask the Web for "tkinter deletecommand". Turns out that somebody
some years ago filed a bug (see bugreport_) which states::

     Tkinter.Menu.delete does not delete the commands
     defined for the entries it deletes. Those objects
     will be retained until the menu itself is deleted.
     [..]
     the command function will still be referenced and
     kept in memory - until the menu object itself is
     destroyed.

Well, this seems to be the root of our memory leak. Let's adapt the `delete`
method a bit, so that the associated commands are deleted as well::

    def delete(self, index1, index2=None):
        """Delete menu items between INDEX1 and INDEX2 (not included)."""
        if index2 is None:
            index2 = index1
        cmds = []
        (num_index1, num_index2) = (self.index(index1), self.index(index2))
        if (num_index1 is not None) and (num_index2 is not None):
            for i in range(num_index1, num_index2 + 1):
                if 'command' in self.entryconfig(i):
                    c = str(self.entrycget(i, 'command'))
                    if c in self._tclCommands:
                        cmds.append(c)
        self.tk.call(self._w, 'delete', index1, index2)
        for c in cmds:
            self.deletecommand(c)

Now we restart IDLE, calibrate our tracker and do another round of `print_diff`.
After the first time the Path Browser is opened we get this::

       types |   # objects |   total size
  ========== | =========== | ============
       tuple |         146 |     13.17 KB
        dict |          13 |     12.01 KB
        list |           2 |     11.26 KB
         str |          92 |      7.59 KB
        code |          46 |      5.52 KB
    function |          45 |      5.40 KB
    classobj |           9 |    864     B
      module |           3 |    168     B

Okay, still some objects created, but no more instances and instance
methods. Let's do it again.::

    types |   # objects |   total size
  ======= | =========== | ============

Yes, this looks definitely better. The memory leak is gone.

The problem is fixed for Python versions 2.5 and higher so updated
installations will not face this leak.
	    

.. 	   http://bugs.python.org/issue1342811
.. 	   http://www.uk.debian.org/~graham/python/tkleak.py


.. _IDLE: http://docs.python.org/lib/idle.html
.. _bugreport: http://bugs.python.org/issue1342811
