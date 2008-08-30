"""Heapmonitor

Facility to introspect memory consumption of certain classes and objects.
Tracked objects are sized recursively to provide an overview of memory
distribution between the different tracked objects.

"""

#
# FIXME __COPYRIGHT__
#
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
# 
#        http://www.apache.org/licenses/LICENSE-2.0
# 
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
# 

#
# The meta programming techniques used to trace object construction requires
# nested scopes introduced in Python 2.2. For Python 2.1 compliance,
# nested_scopes are imported from __future__.
#
from __future__ import nested_scopes

#__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

# FIXME Get set type in Python 2.2/2.3.
#import SCons.compat

import sys
import time

from weakref     import ref as weakref_ref
from new         import instancemethod
from inspect     import stack, getmembers

import cPickle
import gc

import pympler.sizer.asizeof as asizeof
#from SCons.Debug import memory

# Dictionaries of TrackedObject objects associated with the actual objects that
# are tracked. 'tracked_index' uses the class name as the key and associates a
# list of tracked objects. It contains all TrackedObject instances, including
# those of dead objects.
tracked_index = {}

# 'tracked_objects' uses the id (address) as the key and associates the tracked
# object with it. TrackedObject's referring to dead objects are replaced lazily,
# i.e. when the id is recycled by another tracked object.
tracked_objects = {}

# List of (timestamp, size_of_tracked_objects) tuples for each snapshot.
footprint = []

# Keep objects alive by holding a strong reference.
_keepalive = [] 

# Dictionary of class observers identified by classname.
_observers = {}

# Fixpoint for program start relative time stamp.
_local_start = time.time()

# Thread object responsible for background monitoring
_periodic_thread = None

# Lock that protects `create_snapshot`
_snapshot_lock = None 

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

def _is_tracked(klass):
    """
    Determine if the class is tracked.
    """
    return _observers.has_key(klass)

def _track_modify(klass, name, detail, keep, trace):
    """
    Modify settings of a tracked class
    """
    _observers[klass].modify(name, detail, keep, trace)

def _inject_constructor(klass, f, name, resolution_level, keep, trace):
    """
    Modifying Methods in Place - after the recipe 15.7 in the Python
    Cookbook by Ken Seehof. The original constructors may be restored later.
    Therefore, prevent constructor chaining by multiple calls with the same
    class.
    """
    if _is_tracked(klass):
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
    _observers[klass] = _ClassObserver(ki, name, resolution_level, keep, trace)
    klass.__init__ = instancemethod(
        lambda *args, **kwds: f(_observers[klass], *args, **kwds), None, klass)

def _restore_constructor(klass):
    """
    Restore the original constructor, lose track of class.
    """
    klass.__init__ = _observers[klass].init
    del _observers[klass]


def _tracker(_observer_, self, *args, **kwds):
    """
    Injected constructor for tracked classes.
    Call the actual constructor of the object and track the object.
    Attach to the object before calling the constructor to track the object with
    the parameters of the most specialized class.
    """
    track_object(self, name=_observer_.name, resolution_level=_observer_.detail,
        keep=_observer_.keep, trace=_observer_.trace)
    _observer_.init(self, *args, **kwds)

def _trunc(s, max, left=0):
    """
    Convert 's' to string, eliminate newlines and truncate the string to 'max'
    characters. If there are more characters in the string add '...' to the
    string. With 'left=1', the string can be truncated at the beginning.
    """
    s = str(s)
    s = s.replace('\n', '|')
    if len(s) > max:
        if left:
            return '...'+s[len(s)-max+3:]
        else:
            return s[:(max-3)]+'...'
    else:
        return s

def _pp(i):
    degree = 0
    pattern = "%4d     %s"
    while i > 1024:
        pattern = "%7.2f %s"
        i = i / 1024.0
        degree += 1
    scales = ['B', 'KB', 'MB', 'GB', 'TB', 'EB']
    return pattern % (i, scales[degree])

def _get_timestamp(t):
    """
    Get a friendly timestamp represented as a string.
    """
    if t is None: 
        return ''
    h, m, s = int(t / 3600), int(t / 60 % 60), t % 60
    return "%02d:%02d:%05.2f" % (h, m, s)

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
        for key, value in state.items():
            setattr(self, key, value)        

    def _print_refs(self, file, refs, total, prefix='    ', level=1, 
        minsize=0, minpct=0.1):
        """
        Print individual referents recursively.
        """
        lcmp = lambda i, j: (i.size > j.size) and -1 or (i.size < j.size) and 1 or 0
        lrefs = list(refs)
        lrefs.sort(lcmp)
        for r in lrefs:
            if r.size > minsize and (r.size*100.0/total) > minpct:
                file.write('%-50s %-14s %3d%% [%d]\n' % (_trunc(prefix+str(r.name),50),
                    _pp(r.size),int(r.size*100.0/total), level))
                self._print_refs(file, r.refs, total, prefix=prefix+'  ', level=level+1)

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

    def print_text(self, file, full=0):
        """
        Print the gathered information in human-readable format to the specified
        file.
        """
        if full:
            if self.death:
                file.write('%-32s ( free )   %-35s\n' % (
                    _trunc(self.name, 32, left=1), _trunc(self.repr, 35)))
            else:
                file.write('%-32s 0x%08x %-35s\n' % (
                    _trunc(self.name, 32, left=1), self.id, _trunc(self.repr, 35)))
            try:
                for line in self.trace:
                    file.write(line)
            except AttributeError:
                pass
            for (ts, size) in self.footprint:
                file.write('  %-30s %s\n' % (_get_timestamp(ts), _pp(size.size)))
                self._print_refs(file, size.refs, size.size)                    
            if self.death is not None:
                file.write('  %-30s finalize\n' % _get_timestamp(ts))
        else:
            # TODO Print size for largest snapshot (get_size_at_time)
            # Unused ATM: Maybe drop this type of reporting
            size = self.get_max_size()
            if self.repr:
                file.write('%-64s %-14s\n' % (_trunc(self.repr, 64), _pp(size)))
            else:
                file.write('%-64s %-14s\n' % (_trunc(self.name, 64), _pp(size)))       
        

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
            self.repr = _trunc(str(obj), 128)

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
    
    def finalize(self, ref):
        """
        Mark the reference as dead and remember the timestamp.
        It would be great if we could measure the pre-destruction size. 
        Unfortunately, the object is gone by the time the weakref callback is called.
        However, weakref callbacks are useful to be informed when tracked objects died
        without the need of destructors.

        If the object is destroyed at the end of the program execution, it's not
        possible to import modules anymore. Hence, the finalize callback just
        does nothing (self.death stays None).
        """
        try:
            self.death = _get_time()
        except:
            pass


def track_change(instance, resolution_level=0):
    """
    Change tracking options for the already tracked object 'instance'.
    If instance is not tracked, a KeyError will be raised.
    """
    to = tracked_objects[id(instance)]
    to.set_resolution_level(resolution_level)


def track_object(instance, name=None, resolution_level=0, keep=0, trace=0):
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
    if tracked_objects.has_key(id(instance)) and \
        tracked_objects[id(instance)].ref() is not None:
        return

    to = TrackedObject(instance, resolution_level=resolution_level, trace=trace)

    if name is None:
        name = instance.__class__.__name__
    if not tracked_index.has_key(name):
        tracked_index[name] = []
    tracked_index[name].append(to)
    tracked_objects[id(instance)] = to

    #print "DEBUG: Track %s (Keep=%d, Resolution=%d)" % (name, keep, resolution_level)

    if keep:
        _keepalive.append(instance)


def track_class(cls, name=None, resolution_level=0, keep=0, trace=0):
    """
    Track all objects of the class 'cls'. Objects of that type that already
    exist are _not_ tracked. If track_class is called for a class already
    tracked, the tracking parameters are modified. Instantiation traces can be
    generated with trace=1. 
    A constructor is injected to begin instance tracking on creation
    of the object. The constructor calls 'track_object' internally.
    """
    if name is None:
        try:
            name = cls.__module__ + '.' + cls.__name__
        except AttributeError:
            pass
    if _is_tracked(cls):
        _track_modify(cls, name, resolution_level, keep, trace)
    else:
        _inject_constructor(cls, _tracker, name, resolution_level, keep, trace)


def detach_class(klass):
    """ 
    Stop tracking class 'klass'. Any new objects of that type are not
    tracked anymore. Existing objects are still tracked.
    """
    _restore_constructor(klass)


def detach_all_classes():
    """
    Detach from all tracked classes.
    """
    for klass in _observers.keys():
        detach_class(klass) 


def detach_all():
    """
    Detach from all tracked classes and objects.
    Restore the original constructors and cleanse the tracking lists.
    """
    detach_all_classes()
    tracked_objects.clear()
    tracked_index.clear()
    _keepalive[:] = []

def clear():
    """
    Clear all gathered data and detach from all tracked objects/classes.
    """
    detach_all()
    footprint[:] = []

#
# Background Monitoring
#

try:
    import threading
except ImportError:
    pass
else:
    _snapshot_lock = threading.Lock()

    class PeriodicThread(threading.Thread):
        """
        Thread object to take snapshots periodically.
        """    
        def run(self):
            """
            Loop until a stop signal is set.
            """
            self.stop = 0
            while not self.stop:
                create_snapshot()
                time.sleep(self.interval)

    def start_periodic_snapshots(interval=1.0):
        """
        Start a thread which takes snapshots periodically. The `interval` specifies
        the time in seconds the thread waits between taking snapshots. The thread is
        started as a daemon allowing the program to exit. If periodic snapshots are
        already active, the interval is updated.
        """
        global _periodic_thread

        if not _periodic_thread:
            _periodic_thread = PeriodicThread(name='BackgroundMonitor')
            _periodic_thread.setDaemon(True)
            _periodic_thread.interval = interval
            _periodic_thread.start()
        elif _periodic_thread.isAlive():
            _periodic_thread.interval = interval

    def stop_periodic_snapshots():
        """
        Post a stop signal to the thread that takes the periodic snapshots. The
        function waits for the thread to terminate which can take some time
        depending on the configured interval.
        """
        global _periodic_thread

        if _periodic_thread and _periodic_thread.isAlive():
            _periodic_thread.stop = 1
            _periodic_thread.join()
            _periodic_thread = None

#
# Snapshots
#

class Footprint:
    pass

def create_snapshot(description=''):
    """
    Collect current per instance statistics.
    Save total amount of memory consumption reported by asizeof and by the
    operating system. The overhead of the Heapmonitor structure is also
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
        objs = [to.ref() for to in tracked_objects.values()]
        sizer.exclude_refs(*objs)

        # The objects need to be sized in a deterministic order. Sort the
        # objects by its creation date which should at least work for non-parallel
        # execution. The "proper" fix would be to handle shared data separately.
        sorttime = lambda i, j: (i.birth < j.birth) and -1 or (i.birth > j.birth) and 1 or 0
        tos = tracked_objects.values()
        tos.sort(sorttime)
        for to in tos:
            to.track_size(ts, sizer)

        fp = Footprint()

        fp.timestamp = ts
        fp.tracked_total = sizer.total
        if fp.tracked_total:
            fp.asizeof_total = asizeof.asizeof(all=True, code=True)
        else:
            fp.asizeof_total = 0
        fp.system_total = 0 #memory() FIXME
        fp.desc = str(description)

        # Compute overhead of all structures, use sizer to exclude tracked objects(!)
        fp.overhead = 0
        if fp.tracked_total:
            fp.overhead = sizer.asizeof(tracked_index, tracked_objects, footprint)
            fp.asizeof_total -= fp.overhead

        footprint.append(fp)

    finally:
        if _snapshot_lock is not None:
            _snapshot_lock.release()

#
# Off-line Analysis
#

class MemStats:
    """
    Presents the gathered memory statisitics based on user preferences.
    """

    def __init__(self, filename=None, stream=sys.stdout, tracked_index=None, footprint=None):
        """
        Initialize the data log structures.
        """
        self.stream = stream
        self.tracked_index = tracked_index
        self.footprint = footprint
        self.sorted = []
        if filename:
            self.load_stats(filename)
    
    def load_stats(self, file):
        """
        Load the data from a dump file.
        The argument `file` can be either a filename or a an open file object
        that requires read access.
        """
        if isinstance(file, type('')):
            file = open(file, 'r')
        self.tracked_index = cPickle.load(file)
        self.footprint = cPickle.load(file)
        self.sorted = []

    def dump_stats(self, file, close=1):
        """
        Dump the logged data to a file.
        The argument `file` can be either a filename or a an open file object
        that requires write access. `close` controls if the file is closed
        before leaving this method (the default behaviour).
        """
        if isinstance(file, type('')):
            file = open(file, 'w')
        cPickle.dump(tracked_index, file, protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(footprint, file, protocol=cPickle.HIGHEST_PROTOCOL)
        if close:
            file.close()

    def _init_sort(self):
        """
        Prepare the data to be sorted.
        If not yet sorted, import all tracked objects from the tracked index.
        Extend the tracking information by implicit information to make
        sorting easier.
        """
        if not self.sorted:
            # Identify the snapshot that tracked the largest amount of memory.
            tmax = None
            maxsize = 0
            for fp in self.footprint:
                if fp.tracked_total > maxsize:
                    tmax = fp.timestamp
            for key in self.tracked_index.iterkeys():
                for to in self.tracked_index[key]:
                    to.classname = key
                    to.size = to.get_max_size()
                    to.tsize = to.get_size_at_time(tmax)
                self.sorted.extend(self.tracked_index[key])

    def sort_stats(self, *args):
        """
        Sort the tracked objects according to the supplied criteria. The
        argument is a string identifying the basis of a sort (example: 'size' or
        'classname'). When more than one key is provided, then additional keys
        are used as secondary criteria when there is equality in all keys
        selected before them. For example, sort_stats('name', 'size') will sort
        all the entries according to their class name, and resolve all ties
        (identical class names) by sorting by size.  The criteria are fields in
        the tracked object instances. Results are stored in the `self.sorted`
        list which is used by `MemStats.print_stats()` and other methods. The
        fields available for sorting are:

          'classname' : the name with which the class was registered
          'name'      : the classname
          'birth'     : creation timestamp
          'death'     : destruction timestamp
          'size'      : the maximum measured size of the object
          'tsize'     : the measured size during the largest snapshot
          'repr'      : string representation of the object

        Note that sorts on size are in descending order (placing most memory
        consuming items first), whereas name, repr, and creation time searches
        are in ascending order (alphabetical).

        The function returns self to allow calling functions on the result:

        >>> stats.sort_stats('size').reverse_order().print_stats()
        """

        criteria = ('classname', 'tsize', 'birth', 'death', 
                    'name', 'repr', 'size')

        if not set(criteria).issuperset(set(args)):
            raise ValueError, "Invalid sort criteria"

        if not args:
            args = criteria

        def _sort(a, b, crit=args):
            for c in crit:
                res = cmp(getattr(a,c), getattr(b,c))
                if res:
                    if c in ('tsize', 'size', 'death'): 
                        return -res
                    return res
            return 0

        if not self.sorted:
            self._init_sort()

        self.sorted.sort(_sort)

        return self

    def reverse_order(self):
        """
        Reverse the order of the tracked instance index `self.sorted`.
        """
        if not self.sorted:
            self._init_sort()
        self.sorted.reverse()
        return self

    def diff_stats(self, stats):
        raise NotImplementedError

    def annotate_snapshot(self, snapshot):
        """
        Store addition statistical data in snapshot.
        """
        if hasattr(snapshot, 'classes'):
            return

        snapshot.classes = {}

        for classname in self.tracked_index.iterkeys():
            sum = 0
            active = 0
            for to in self.tracked_index[classname]:
                sum += to.get_size_at_time(snapshot.timestamp)
                if to.birth < snapshot.timestamp and (to.death is None or 
                   to.death > snapshot.timestamp):
                    active += 1
            try:
                pct = sum * 100.0 / snapshot.asizeof_total
            except ZeroDivisionError:
                pct = 0
            try:
                avg = sum / active
            except ZeroDivisionError:
                avg = 0

            snapshot.classes[classname] = {'sum': sum, 'avg': avg, 'pct': pct, \
                'active': active}
        
    def print_stats(self, filter=None, limit=1.0):
        """
        Write tracked objects to stdout.  The output can be filtered and pruned.
        Only objects are printed whose classname contain the substring supplied
        by the `filter` argument.  The output can be pruned by passing a limit
        value. If `limit` is a float smaller than one, only the supplied
        percentage of the total tracked data is printed. If `limit` is bigger
        than one, this number of tracked objects are printed. Tracked objects
        are first filtered, and then pruned (if specified).
        """
        if not self.sorted:
            self.sort_stats()

        sorted = self.sorted

        if filter:
            sorted = [to for to in sorted if filter in to.classname]

        if limit < 1.0:
            sorted = sorted[:int(len(self.sorted)*limit)+1]
        elif limit > 1:
            sorted = sorted[:int(limit)]

        # Emit per-instance data
        for to in sorted:
            to.print_text(self.stream, full=1)

    def print_summary(self):
        """
        Print per-class summary for each snapshot.
        """
        # Emit class summaries for each snapshot
        classlist = self.tracked_index.keys()
        classlist.sort()

        file = self.stream

        file.write('---- SUMMARY '+'-'*66+'\n')
        for fp in self.footprint:
            self.annotate_snapshot(fp)
            file.write('%-35s %11s %12s %12s %5s\n' % \
                (_trunc(fp.desc, 35), 'active', _pp(fp.asizeof_total), 
                 'average', 'pct'))
            for classname in classlist:
                info = fp.classes[classname]
                sum, avg, pct, active = info['sum'], info['avg'], info['pct'], info['active']
                file.write('  %-33s %11d %12s %12s %4d%%\n' % \
                    (_trunc(classname, 33), active, _pp(sum), _pp(avg), pct))
        file.write('-'*79+'\n')

class HtmlStats(MemStats):
    """
    Output the Heapmonitor statistics as HTML pages and graphs.
    """

    style          = """<style type="text/css">
        table { width:100%; border:1px solid #000; border-spacing:0px; }
        td, th { border:0px; }
        #nb { border:0px; }
        #tl { margin-top:5mm; margin-bottom:5mm; }
        #p1 { padding-left: 5px; }
        #p2 { padding-left: 50px; }
        #p3 { padding-left: 100px; }
        #p4 { padding-left: 150px; }
        #p5 { padding-left: 200px; }
        #p6 { padding-left: 210px; }
        #p7 { padding-left: 220px; }
        #hl { background-color:#FFFFCC; }
        #r1 { background-color:#BBBBBB; }
        #r2 { background-color:#CCCCCC; }
        #r3 { background-color:#DDDDDD; }
        #r4 { background-color:#EEEEEE; }
        #r5,#r6,#r7 { background-color:#FFFFFF; }
        #num { text-align:right; }
    </style>
    """

    nopylab_msg    = """<div>Could not generate %s chart!
    Install <a href=http://matplotlib.sourceforge.net/">Matplotlib</a> 
    to generate charts.</div>\n"""

    chart_tag      = '<img src="%s">\n'
    header         = "<html><head><title>%s</title>%s</head><body>\n"
    tableheader    = '<table border="1">\n'
    tablefooter    = '</table>\n'
    footer         = '</body></html>\n'

    refrow = """<tr id="r%(level)d">
        <td id="p%(level)d">%(name)s</td>
        <td id="num">%(size)s</td>
        <td id="num">%(pct)3.1f%%</td></tr>"""

    def _print_refs(self, file, refs, total, level=1, minsize=0, minpct=0.1):
        """
        Print individual referents recursively.
        """
        lcmp = lambda i, j: (i.size > j.size) and -1 or (i.size < j.size) and 1 or 0
        lrefs = list(refs)
        lrefs.sort(lcmp)
        if level == 1:
            file.write('<table>\n')
        for r in lrefs:
            if r.size > minsize and (r.size*100.0/total) > minpct:
                data = {'level': level, 'name': _trunc(str(r.name),128),
                    'size': _pp(r.size), 'pct': r.size*100.0/total }
                file.write(self.refrow % data)
                self._print_refs(file, r.refs, total, level=level+1)
        if level == 1:
            file.write("</table>\n")

    class_summary = """<p>%(cnt)d instances of %(cls)s were registered. The
    average size is %(avg)s, the minimal size is %(min)s, the maximum size is
    %(max)s.</p>\n"""

    def print_class_details(self, fname, classname):
        """
        Print detailed statistics and instances for the class `classname`. All
        data will be written to the file `fname`.
        """
        file = open(fname, "w")
        file.write(self.header % (classname, self.style))

        file.write("<h1>%s</h1>\n" % (classname))

        sizes = [to.get_max_size() for to in self.tracked_index[classname]]
        sum = reduce( lambda s,x: s+x, sizes )
        data = {'cnt': len(self.tracked_index[classname]), 'cls': classname}
        data['avg'] = _pp(sum / len(sizes))
        data['max'] = _pp(max(sizes))
        data['min'] = _pp(min(sizes))
        file.write(self.class_summary % data)

        file.write(self.charts[classname])

        file.write("<h2>Instances</h2>\n")
        for to in self.tracked_index[classname]:
            file.write('<table id="tl" width="100%" rules="rows">\n')
            file.write('<tr><td id="hl" width="140px">Instance</td><td id="hl">%s at 0x%08x</td></tr>\n' % (to.name, to.id))
            if to.repr:
                file.write("<tr><td>Representation</td><td>%s&nbsp;</td></tr>\n" % to.repr)
            file.write("<tr><td>Lifetime</td><td>%s - %s</td></tr>\n" % (_get_timestamp(to.birth), _get_timestamp(to.death)))
            if hasattr(to, 'trace'):
                trace = "<pre>%s</pre>" % (''.join(to.trace))                
                file.write("<tr><td>Instantiation</td><td>%s</td></tr>\n" % trace)
            for (ts, size) in to.footprint:
                file.write("<tr><td>%s</td>" % _get_timestamp(ts))
                if not size.refs:
                    file.write("<td>%s</td></tr>\n" % _pp(size.size))
                else:
                    file.write("<td>%s" % _pp(size.size))
                    self._print_refs(file, size.refs, size.size)
                    file.write("</td></tr>\n")
            file.write("</table>\n")

        file.write(self.footer)    
        file.close()
    
    snapshot_cls_header = """<tr>
        <th id="hl">Class</th>
        <th id="hl" align="right">Instance #</th>
        <th id="hl" align="right">Total</th>
        <th id="hl" align="right">Average size</th>
        <th id="hl" align="right">Share</th></tr>\n"""

    snapshot_cls = """<tr>
        <td>%(cls)s</td>
        <td align="right">%(active)d</td>
        <td align="right">%(sum)s</td>
        <td align="right">%(avg)s</td>
        <td align="right">%(pct)3.2f%%</td></tr>\n"""

    snapshot_summary = """<p>Total virtual memory assigned to the program at that time
        was %(sys)s, which includes %(overhead)s profiling overhead. The
        Heapmonitor tracked %(tracked)s in total. The measurable objects
        including code objects but excluding overhead have a total size of
        %(asizeof)s.</p>\n"""

    def print_summary(self, filename, title=''):
        """
        Output the title page.
        """
        file = open(filename, "w")
        file.write(self.header % (title, self.style))

        file.write("<h1>%s</h1>\n" % title)
        file.write("<h2>Memory distribution over time</h2>\n")
        file.write(self.charts['snapshots'])

        file.write("<h2>Snapshots statistics</h2>\n")
        file.write('<table id="nb">\n')

        classlist = self.tracked_index.keys()
        classlist.sort()

        for fp in self.footprint:
            file.write('<tr><td>\n')
            file.write('<table id="tl" rules="rows">\n')
            self.annotate_snapshot(fp)
            file.write("<h3>%s snapshot at %s</h3>\n" % (fp.desc or 'Untitled',\
                _get_timestamp(fp.timestamp)))

            data = {}
            data['sys']      = _pp(fp.system_total)
            data['tracked']  = _pp(fp.tracked_total)
            data['asizeof']  = _pp(fp.asizeof_total)
            data['overhead'] = _pp(getattr(fp, 'overhead', 0))

            file.write(self.snapshot_summary % data)

            if fp.tracked_total:
                file.write(self.snapshot_cls_header)
                for classname in classlist:
                    data = fp.classes[classname].copy()
                    data['cls'] = "<a href='%s'>%s</a>" % (self.links[classname], classname)
                    data['sum'] = _pp(data['sum'])
                    data['avg'] = _pp(data['avg'])
                    file.write(self.snapshot_cls % data)
            file.write('</table>')
            file.write('</td><td>\n')
            if fp.tracked_total:
                file.write(self.charts[fp])
            file.write('</td></tr>\n')

        file.write("</table>\n")
        file.write(self.footer)    
        file.close()

    def create_lifetime_chart(self, classname, filename=''):
        """
        Create chart that depicts the lifetime of the instance registered with
        `classname`. The output is written to `filename`.
        """
        try:
            from pylab import figure, title, xlabel, ylabel, plot, savefig
        except ImportError:
            return HtmlStats.nopylab_msg % (classname+" lifetime")

        cnt = []
        for to in self.tracked_index[classname]:
            cnt.append([to.birth, 1])
            if to.death:
                cnt.append([to.death, -1])
        cnt.sort()
        for i in xrange(1, len(cnt)):
            cnt[i][1] += cnt[i-1][1]
            #if cnt[i][0] == cnt[i-1][0]:
            #    del cnt[i-1]

        x = [t for [t,c] in cnt]
        y = [c for [t,c] in cnt]

        figure()
        xlabel("Execution time [s]")
        ylabel("Instance #")
        title("%s instances" % classname)
        plot(x, y, 'o')
        savefig(filename)

        return HtmlStats.chart_tag % (filename)
    
    def create_snapshot_chart(self, filename=''):
        """
        Create chart that depicts the memory allocation over time apportioned to
        the tracked classes.
        """
        try:
            from pylab import figure, title, xlabel, ylabel, plot, fill, legend, savefig
            import matplotlib.mlab as mlab
        except ImportError:
            return self.nopylab_msg % ("memory allocation")

        for fp in self.footprint:
            self.annotate_snapshot(fp)

        classlist = self.tracked_index.keys()
        classlist.sort()

        x = [fp.timestamp for fp in self.footprint]
        base = [0] * len(self.footprint)
        poly_labels = []
        polys = []
        for cn in classlist:
            pct = [fp.classes[cn]['pct'] for fp in self.footprint]
            if max(pct) > 3.0:
                sz = [float(fp.classes[cn]['sum'])/(1024*1024) for fp in self.footprint]
                sz = map( lambda x, y: x+y, base, sz )
                xp, yp = mlab.poly_between(x, base, sz)
                polys.append( ((xp, yp), {'label': cn}) )
                poly_labels.append(cn)
                base = sz
       
        figure()
        title("Snapshot Memory")
        xlabel("Execution Time [s]")
        ylabel("Virtual Memory [MiB]")

        y = [float(fp.asizeof_total)/(1024*1024) for fp in self.footprint]
        plot(x, y, 'r--', label='Total')
        y = [float(fp.tracked_total)/(1024*1024) for fp in self.footprint]
        plot(x, y, 'b--', label='Tracked total')
        
        for (args, kwds) in polys:
            fill(*args, **kwds)
        legend(loc=2)
        savefig(filename)

        return self.chart_tag % (filename)

    def create_pie_chart(self, snapshot, filename=''):
        """
        Create a pie chart that depicts the distribution of the allocated memory
        for a given `snapshot`. The chart is saved to `filename`.
        """
        try:
            from pylab import figure, title, pie, axes, savefig, sum
        except ImportError:
            return self.nopylab_msg % (classname+" lifetime")

        # Don't bother illustrating a pie without pieces.
        if not snapshot.tracked_total:
            return ''

        self.annotate_snapshot(snapshot)
        classlist = []
        sizelist = []
        for k, v in snapshot.classes.items():
            if v['pct'] > 3.0:
                classlist.append(k)
                sizelist.append(v['sum'])
        sizelist.insert(0, snapshot.asizeof_total - sum(sizelist))
        classlist.insert(0, 'Other')
        #sizelist = [x*0.01 for x in sizelist]

        title("Snapshot (%s) Memory Distribution" % (snapshot.desc))
        figure(figsize=(8,8))
        axes([0.1, 0.1, 0.8, 0.8])
        pie(sizelist, labels=classlist)
        savefig(filename, dpi=50)

        return self.chart_tag % (filename)

    def create_html(self, fname, title="Heapmonitor Statistics"):
        """
        Create HTML page `fname` and additional files in a directory derived
        from `fname`.
        """
        from os import path, mkdir

        # Create a folder to store the charts and additional HTML files.
        self.filesdir = path.splitext(fname)[0] + '_files'
        if not path.isdir(self.filesdir):
            mkdir(self.filesdir)
        self.filesdir = path.abspath(self.filesdir)
        self.links = {}

        # Create charts. The tags to show the images are returned and stored in
        # the self.charts dictionary. This allows to return alternative text if
        # the chart creation framework is not available.
        self.charts = {}
        fn = path.join(self.filesdir, 'timespace.png')
        self.charts['snapshots'] = self.create_snapshot_chart(fn)

        for fp, idx in map(None, self.footprint, range(len(self.footprint))):
            fn = path.join(self.filesdir, 'fp%d.png' % (idx))
            self.charts[fp] = self.create_pie_chart(fp, fn)

        for cn in self.tracked_index.iterkeys():
            fn = path.join(self.filesdir, cn.replace('.', '_')+'-lt.png')
            self.charts[cn] = self.create_lifetime_chart(cn, fn)

        # Create HTML pages first for each class and then the index page.
        for cn in self.tracked_index.iterkeys():
            fn = path.join(self.filesdir, cn.replace('.', '_')+'.html')
            self.links[cn]  = fn
            self.print_class_details(fn, cn)

        self.print_summary(fname, title=title)
    

def dump_stats(file, close=1):
    """
    Dump the logged data to `file`. Stop asynchronous snapshots to prevent the
    data of changing while being dumped. The side effect are lags, especially
    when a long period has been set. As dumping and loading are time-intensive
    operations when there is a large amount of data, allow creating HTML
    documents directly if a filename with a '.html' suffix is passed.
    """
    stop_periodic_snapshots()
    if isinstance(file, type('')) and file[-5:] == '.html':
        stats = HtmlStats(tracked_index=tracked_index, footprint=footprint)
        stats.create_html(file)
    else:
        stats = MemStats(tracked_index=tracked_index, footprint=footprint)
        stats.dump_stats(file, close)

def print_stats(file=sys.stdout):
    """
    Write tracked objects by class to stdout. Stop asynchronous snapshots to
    prevent the data of changing while being printed. The side effect are lags,
    especially when a long period has been set. 
    """
    stop_periodic_snapshots()
    stats = MemStats(stream=file, tracked_index=tracked_index, footprint=footprint)
    stats.print_stats()
    stats.print_summary()

def print_snapshots(file=sys.stdout):
    """
    Print snapshot stats.
    """
    file.write('%-32s %15s (%11s) %15s\n' % ('Snapshot Label', 'Virtual Total',
        'Measurable', 'Tracked Total'))
    for fp in footprint:
        label = fp.desc
        if label == '':
            label = _get_timestamp(fp.timestamp)
        sample = "%-32s %15s (%11s) %15s\n" % \
            (label, _pp(fp.system_total), _pp(fp.asizeof_total), 
            _pp(fp.tracked_total))
        file.write(sample)


#
# Garbage collection.
# Use the data exposed by the garbage collector to present the data in a
# meaningful and user-friendly way.
#

graphviz_file = None

class Garbage:
    pass

def _log_garbage(garbage, file=sys.stdout):
    """
    Log garbage to console.
    """
    sz = 0
    sortgarbage = lambda a, b: \
        a.size > b.size and -1 or \
        a.size < b.size and 1 or 0
    garbage.sort(sortgarbage)
    file.write('%-10s %8s %-12s %-46s\n' % ('id', 'size', 'type', 'representation'))
    for g in garbage:
        sz += g.size
        file.write('0x%08x %8d %-12s %-46s\n' % (g.id, g.size, _trunc(g.type, 12),
            _trunc(g.str, 46)))

def _visualize_gc_graphviz(garbage, metagarbage, edges, file):
    """
    Emit a graph representing the connections between the objects collected by
    the garbage collector. The text representation can be transformed to a graph
    with graphviz.
    The file has to permit write access and is closed at the end of the
    function.
    """
    header = '// Process this file with graphviz\n'
    file.write(header)
    file.write('digraph G {\n')
    for n, g in map(None, garbage, metagarbage):
        label = _trunc(g.str, 48).replace('"', "'")
        extra = ''
        if g.type == 'instancemethod':
            extra = ', color=red'
        elif g.type == 'frame':
            extra = ', color=orange'
        file.write('    "X%08x" [ label = "%s\\n%s" %s ];\n' % \
            (id(n), label, g.type, extra))
    for (i, j, l) in edges:
        file.write('    X%08x -> X%08x [label="%s"];\n' % (i, j, l))

    file.write('}\n')
    file.close()

if hasattr(gc, 'get_referents'):
    def eliminate_leafs(graph, get_referents=gc.get_referents):
        """
        Eliminate leaf objects (not directly part of cycles).
        """
        result = []
        idset = set([id(x) for x in graph])
        for n in graph:
            refset = set([id(x) for x in get_referents(n)])
            if refset.intersection(idset):
                result.append(n)
        return result

    def get_edges(graph, get_referents=gc.get_referents):
        """
        Compute the edges for the reference graph.
        The function returns a set of tuples (id(a), id(b), ref) if a
        references b with the referent 'ref'.
        """
        idset = set([id(x) for x in graph])
        edges = set([])
        for n in graph:
            refset = set([id(x) for x in get_referents(n)])
            for ref in refset.intersection(idset):
                label = ''
                for (k, v) in getmembers(n):
                    if id(v) == ref:
                        label = k
                        break
                edges.add((id(n), ref, label))
        return edges

else:
    # TODO Implement the functions using get_referrers instead of get_referents
    # for Python 2.2 compliance.
    def eliminate_leafs(graph, get_referents=None, get_referrers=gc.get_referrers):
        return graph

    def get_edges(graph, get_referents=None, get_referrers=gc.get_referrers):
        return set([])


def find_garbage(sizer=None, graphfile=None, prune=1):
    """
    Let the garbage collector identify ref cycles.
    First, the garbage collector runs and saves the garbage into gc.garbage. The
    leafs of the reference graph will be pruned to only include objects directly
    involved in actual cycles. The remaining garbage elements will be sized
    (which will include the pruned leaf sizes) and annotated. If a graphfile is
    passed and garbage was detected, the garbage will be visualized in graphviz
    format.
    The total number of garbage and the annotated cycle elements are returned.
    """
    if not sizer:
        sizer = asizeof.Asizer()

    gc.set_debug(gc.DEBUG_SAVEALL)
    gc.collect()

    total = len(gc.garbage)
    cnt = 0
    cycles = gc.garbage[:]

    if prune:
        while cnt != len(cycles):
            cnt = len(cycles)
            cycles = eliminate_leafs(cycles)

    edges = get_edges(cycles)

    garbage = []
    for obj, sz in map(None, cycles, sizer.asizesof(*cycles)):
        g = Garbage()
        g.size = sz
        g.id = id(obj)
        try:
            g.type = obj.__class__.__name__
        except (AttributeError, ReferenceError):
            g.type = type(obj)
        try:
            g.str = _trunc(str(obj), 128)
        except ReferenceError:
            g.str = ''
        garbage.append(g)
    
    if graphfile and len(garbage) > 0:
        _visualize_gc_graphviz(cycles, garbage, edges, graphfile)

    return total, garbage

def print_garbage_stats(file=sys.stdout):
    """
    Print statistics related to garbage/leaks.
    """

    f = None
    if graphviz_file:
        f = open(graphviz_file, 'w')

    sizer = asizeof.Asizer()
    total, garbage = find_garbage(sizer, f)
    sz = sizer.total

    cnt = len(garbage)
    if cnt and graphviz_file:
        file.write("Garbage reference graph saved to: %s\n" % graphviz_file)
    elif cnt:
        _log_garbage(garbage, file)
    file.write('Garbage: %8d collected objects (%6d in cycles): %12s\n' % (total, cnt, _pp(sz)))

