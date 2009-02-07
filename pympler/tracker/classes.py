"""
The `ClassTracker` is a facility delivering insight into the memory distribution
of a Python program. It can introspect memory consumption of certain classes and
objects. Facilities are provided to track and size individual objects or all
instances of certain classes. Tracked objects are sized recursively to provide
an overview of memory distribution between the different tracked objects.
"""
import time

from weakref     import ref as weakref_ref
from pympler.util.compat2and3 import instancemethod
import pympler.asizeof as asizeof
import pympler.process

from inspect import stack
from pympler.util.stringutils import trunc, pp, pp_timestamp

__all__ = ["ClassTracker"]

# Fixpoint for program start relative time stamp.
_local_start = time.time()


class _ClassObserver(object):
    """
    Stores options for tracked classes.
    The observer also keeps the original constructor of the observed class.
    """
    __slots__ = ('init', 'name', 'detail', 'keep', 'trace')

    def __init__(self, init, name, detail, keep, trace):
        self.init = init
        self.name = name
        self.detail = detail
        self.keep = keep
        self.trace = trace

    def modify(self, name, detail, keep, trace):
        self.name = name
        self.detail = detail
        self.keep = keep
        self.trace = trace


def _get_time():
    """
    Get a timestamp relative to the program start time.
    """
    return time.time() - _local_start

class TrackedObject(object):
    """
    Stores size and lifetime information of a tracked object. A weak reference is
    attached to monitor the object without preventing its deletion.
    """
    __slots__ = ("ref", "id", "repr", "name", "birth", "death", "trace",
        "footprint", "_resolution_level", "__dict__")

    def __init__(self, instance, resolution_level=0, trace=0):
        """
        Create a weak reference for 'instance' to observe an object but which
        won't prevent its deletion (which is monitored by the finalize
        callback). The size of the object is recorded in 'footprint' as 
        (timestamp, size) tuples.
        """
        self.ref = weakref_ref(instance, self.finalize)
        self.id = id(instance)
        self.repr = ''
        self.name = str(instance.__class__)
        self.birth = _get_time()
        self.death = None
        self._resolution_level = resolution_level

        if trace:
            self._save_trace()

        initial_size = asizeof.basicsize(instance) or 0
        so = asizeof.Asized(initial_size, initial_size)
        self.footprint = [(self.birth, so)]

    def __getstate__(self):
        """
        Make the object serializable for dump_stats. Read the available slots
        and store the values in a dictionary. Derived values (stored in the
        dict) are not pickled as those can be reconstructed based on the other
        data. References cannot be serialized, ignore 'ref' as well.
        """
        state = {}
        for name in getattr(TrackedObject, '__slots__', ()):
            if hasattr(self, name) and name not in ['ref', '__dict__']:
                state[name] = getattr(self, name)
        return state

    def __setstate__(self, state):
        """
        Restore the state from pickled data. Needed because a slotted class is
        used.
        """
        for key, value in list(state.items()):
            setattr(self, key, value)        

    def _print_refs(self, fobj, refs, total, prefix='    ', level=1, 
        minsize=0, minpct=0.1):
        """
        Print individual referents recursively.
        """
        lrefs = list(refs)
        lrefs.sort(key=lambda x: x.size)
        lrefs.reverse()
        for r in lrefs:
            if r.size > minsize and (r.size*100.0/total) > minpct:
                fobj.write('%-50s %-14s %3d%% [%d]\n' % (trunc(prefix+str(r.name),50),
                    pp(r.size),int(r.size*100.0/total), level))
                self._print_refs(fobj, r.refs, total, prefix=prefix+'  ', level=level+1)

    def _save_trace(self):
        """
        Save current stack trace as formatted string.
        """
        st = stack()
        try:
            self.trace = []
            for f in st[5:]: # eliminate our own overhead
                for l in f[4]:
                    self.trace.insert(0, '    '+l.strip()+'\n')
                self.trace.insert(0, '  %s:%d in %s\n' % (f[1], f[2], f[3]))
        finally:
            del st

    def print_text(self, fobj, full=0):
        """
        Print the gathered information in human-readable format to the specified
        fobj.
        """
        if full:
            if self.death:
                fobj.write('%-32s ( free )   %-35s\n' % (
                    trunc(self.name, 32, left=1), trunc(self.repr, 35)))
            else:
                fobj.write('%-32s 0x%08x %-35s\n' % (
                    trunc(self.name, 32, left=1), self.id, trunc(self.repr, 35)))
            try:
                for line in self.trace:
                    fobj.write(line)
            except AttributeError:
                pass
            for (ts, size) in self.footprint:
                fobj.write('  %-30s %s\n' % (pp_timestamp(ts), pp(size.size)))
                self._print_refs(fobj, size.refs, size.size)                    
            if self.death is not None:
                fobj.write('  %-30s finalize\n' % pp_timestamp(ts))
        else:
            # TODO Print size for largest snapshot (get_size_at_time)
            # Unused ATM: Maybe drop this type of reporting
            size = self.get_max_size()
            if self.repr:
                fobj.write('%-64s %-14s\n' % (trunc(self.repr, 64), pp(size)))
            else:
                fobj.write('%-64s %-14s\n' % (trunc(self.name, 64), pp(size)))       
        

    def track_size(self, ts, sizer):
        """
        Store timestamp and current size for later evaluation.
        The 'sizer' is a stateful sizing facility that excludes other tracked
        objects.
        """
        obj = self.ref()
        self.footprint.append( 
            (ts, sizer.asized(obj, detail=self._resolution_level)) 
        )
        if obj is not None:
            self.repr = trunc(str(obj), 128)

    def get_max_size(self):
        """
        Get the maximum of all sampled sizes, or return 0 if no samples were
        recorded.
        """
        try:
            return max([s.size for (t, s) in self.footprint])
        except ValueError:
            return 0

    def get_size_at_time(self, ts):
        """
        Get the size of the object at a specific time (snapshot).
        If the object was not alive/sized at that instant, return 0.
        """
        for (t, s) in self.footprint:
            if t == ts:
                return s.size
        return 0

    def set_resolution_level(self, resolution_level):
        """
        Set resolution level to a new value. The next size estimation will
        respect the new value. This is useful to set different levels for
        different instances of tracked classes.
        """
        self._resolution_level = resolution_level
    
    def finalize(self, ref): #PYCHOK required to match callback
        """
        Mark the reference as dead and remember the timestamp.  It would be
        great if we could measure the pre-destruction size.  Unfortunately, the
        object is gone by the time the weakref callback is called.  However,
        weakref callbacks are useful to be informed when tracked objects died
        without the need of destructors.

        If the object is destroyed at the end of the program execution, it's not
        possible to import modules anymore. Hence, the finalize callback just
        does nothing (self.death stays None).
        """
        try:
            self.death = _get_time()
        except:
            pass

try:
    import threading
except ImportError:
    threading = 0
else:
    _snapshot_lock = threading.Lock()

    class PeriodicThread(threading.Thread):
        """
        Thread object to take snapshots periodically.
        """
        def __init__(self, tracker, interval, *args, **kw):
            self.interval = interval
            self.tracker = tracker
            threading.Thread.__init__(self, *args, **kw)

        def run(self):
            """
            Loop until a stop signal is set.
            """
            self.stop = 0
            while not self.stop:
                self.tracker.create_snapshot()
                time.sleep(self.interval)

class Footprint(object):
    def __init__(self):
        self.tracked_total = 0
        self.asizeof_total = 0
        self.overhead = 0


class ClassTracker(object):

    def __init__(self):
        # Dictionaries of TrackedObject objects associated with the actual
        # objects that are tracked. 'index' uses the class name as the key and
        # associates a list of tracked objects. It contains all TrackedObject
        # instances, including those of dead objects.
        self.index = {}

        # 'objects' uses the id (address) as the key and associates the tracked
        # object with it. TrackedObject's referring to dead objects are replaced
        # lazily, i.e. when the id is recycled by another tracked object.
        self.objects = {}

        # List of (timestamp, size_of_self.objects) tuples for each snapshot.
        self.footprint = []

        # Keep objects alive by holding a strong reference.
        self._keepalive = [] 

        # Dictionary of class observers identified by classname.
        self._observers = {}

        # Thread object responsible for background monitoring
        self._periodic_thread = None

    def _tracker(self, _observer_, _self_, *args, **kwds):
        """
        Injected constructor for tracked classes.
        Call the actual constructor of the object and track the object.
        Attach to the object before calling the constructor to track the object with
        the parameters of the most specialized class.
        """
        self.track_object(_self_, name=_observer_.name, resolution_level=_observer_.detail,
            keep=_observer_.keep, trace=_observer_.trace)
        _observer_.init(_self_, *args, **kwds)


    def _inject_constructor(self, klass, f, name, resolution_level, keep, trace):
        """
        Modifying Methods in Place - after the recipe 15.7 in the Python
        Cookbook by Ken Seehof. The original constructors may be restored later.
        Therefore, prevent constructor chaining by multiple calls with the same
        class.
        """
        if self._is_tracked(klass):
            return

        try:
            ki = klass.__init__
        except AttributeError:
            def ki(self, *args, **kwds):
                pass

        # Possible name clash between keyword arguments of the tracked class'
        # constructor and the curried arguments of the injected constructor.
        # Therefore, the additional arguments have 'magic' names to make it less
        # likely that an argument name clash occurs.
        self._observers[klass] = _ClassObserver(ki, name, resolution_level, keep, trace)
        klass.__init__ = instancemethod(
            lambda *args, **kwds: f(self._observers[klass], *args, **kwds), None, klass)

    def _is_tracked(self, klass):
        """
        Determine if the class is tracked.
        """
        return klass in self._observers

    def _track_modify(self, klass, name, detail, keep, trace):
        """
        Modify settings of a tracked class
        """
        self._observers[klass].modify(name, detail, keep, trace)

    def _restore_constructor(self, klass):
        """
        Restore the original constructor, lose track of class.
        """
        klass.__init__ = self._observers[klass].init
        del self._observers[klass]

        
    def track_change(self, instance, resolution_level=0):
        """
        Change tracking options for the already tracked object 'instance'.
        If instance is not tracked, a KeyError will be raised.
        """
        to = self.objects[id(instance)]
        to.set_resolution_level(resolution_level)


    def track_object(self, instance, name=None, resolution_level=0, keep=0, trace=0):
        """
        Track object 'instance' and sample size and lifetime information.
        Not all objects can be tracked; trackable objects are class instances and
        other objects that can be weakly referenced. When an object cannot be
        tracked, a TypeError is raised.
        The 'resolution_level' is the recursion depth up to which referents are
        sized individually. Resolution level 0 (default) treats the object as an
        opaque entity, 1 sizes all direct referents individually, 2 also sizes the
        referents of the referents and so forth.
        To prevent the object's deletion a (strong) reference can be held with
        'keep'.
        """

        # Check if object is already tracked. This happens if track_object is called
        # multiple times for the same object or if an object inherits from multiple
        # tracked classes. In the latter case, the most specialized class wins.
        # To detect id recycling, the weak reference is checked. If it is 'None' a
        # tracked object is dead and another one takes the same 'id'. 
        if id(instance) in self.objects and \
            self.objects[id(instance)].ref() is not None:
            return

        to = TrackedObject(instance, resolution_level=resolution_level, trace=trace)

        if name is None:
            name = instance.__class__.__name__
        if not name in self.index:
            self.index[name] = []
        self.index[name].append(to)
        self.objects[id(instance)] = to

        #print "DEBUG: Track %s (Keep=%d, Resolution=%d)" % (name, keep, resolution_level)

        if keep:
            self._keepalive.append(instance)


    def track_class(self, cls, name=None, resolution_level=0, keep=0, trace=0):
        """
        Track all objects of the class `cls`. Objects of that type that already
        exist are *not* tracked. If `track_class` is called for a class already
        tracked, the tracking parameters are modified. Instantiation traces can be
        generated by setting `trace` to True. 
        A constructor is injected to begin instance tracking on creation
        of the object. The constructor calls `track_object` internally.
        """
        if name is None:
            try:
                name = cls.__module__ + '.' + cls.__name__
            except AttributeError:
                pass
        if self._is_tracked(cls):
            self._track_modify(cls, name, resolution_level, keep, trace)
        else:
            self._inject_constructor(cls, self._tracker, name, resolution_level, keep, trace)


    def detach_class(self, klass):
        """ 
        Stop tracking class 'klass'. Any new objects of that type are not
        tracked anymore. Existing objects are still tracked.
        """
        self._restore_constructor(klass)


    def detach_all_classes(self):
        """
        Detach from all tracked classes.
        """
        classes = list(self._observers.keys())
        for klass in classes:
            self.detach_class(klass) 


    def detach_all(self):
        """
        Detach from all tracked classes and objects.
        Restore the original constructors and cleanse the tracking lists.
        """
        self.detach_all_classes()
        self.objects.clear()
        self.index.clear()
        self._keepalive[:] = []

    def clear(self):
        """
        Clear all gathered data and detach from all tracked objects/classes.
        """
        self.detach_all()
        self.footprint[:] = []

#
# Background Monitoring
#

    def start_periodic_snapshots(self, interval=1.0):
        """
        Start a thread which takes snapshots periodically. The `interval` specifies
        the time in seconds the thread waits between taking snapshots. The thread is
        started as a daemon allowing the program to exit. If periodic snapshots are
        already active, the interval is updated.
        """
        if not threading:
            raise NotImplementedError

        if not self._periodic_thread:
            self._periodic_thread = PeriodicThread(self, interval, name='BackgroundMonitor')
            self._periodic_thread.setDaemon(True)
            self._periodic_thread.start()
        elif self._periodic_thread.isAlive():
            self._periodic_thread.interval = interval

    def stop_periodic_snapshots(self):
        """
        Post a stop signal to the thread that takes the periodic snapshots. The
        function waits for the thread to terminate which can take some time
        depending on the configured interval.
        """
        if not threading:
            raise NotImplementedError

        if self._periodic_thread and self._periodic_thread.isAlive():
            self._periodic_thread.stop = 1
            self._periodic_thread.join()
            self._periodic_thread = None

#
# Snapshots
#

    def create_snapshot(self, description=''):
        """
        Collect current per instance statistics.
        Save total amount of memory consumption reported by asizeof and by the
        operating system. The overhead of the ClassTracker structure is also
        computed.
        """

        ts = _get_time()

        try:
            # Snapshots can be taken asynchronously. Prevent race conditions when
            # two snapshots are taken at the same time. TODO: It is not clear what
            # happens when memory is allocated/released while this function is
            # executed but it will likely lead to inconsistencies. Either pause all
            # other threads or don't size individual objects in asynchronous mode.
            if _snapshot_lock is not None:
                _snapshot_lock.acquire()

            sizer = asizeof.Asizer()
            objs = [to.ref() for to in list(self.objects.values())]
            sizer.exclude_refs(*objs)

            # The objects need to be sized in a deterministic order. Sort the
            # objects by its creation date which should at least work for non-parallel
            # execution. The "proper" fix would be to handle shared data separately.
            tos = list(self.objects.values())
            #sorttime = lambda i, j: (i.birth < j.birth) and -1 or (i.birth > j.birth) and 1 or 0
            #tos.sort(sorttime)
            tos.sort(key=lambda x: x.birth)
            for to in tos:
                to.track_size(ts, sizer)

            fp = Footprint()

            fp.timestamp = ts
            fp.tracked_total = sizer.total
            if fp.tracked_total:
                fp.asizeof_total = asizeof.asizeof(all=True, code=True)
            else:
                fp.asizeof_total = 0
            fp.system_total = pympler.process.ProcessMemoryInfo()
            fp.desc = str(description)

            # Compute overhead of all structures, use sizer to exclude tracked objects(!)
            fp.overhead = 0
            if fp.tracked_total:
                fp.overhead = sizer.asizeof(self)
                fp.asizeof_total -= fp.overhead

            self.footprint.append(fp)

        finally:
            if _snapshot_lock is not None:
                _snapshot_lock.release()

