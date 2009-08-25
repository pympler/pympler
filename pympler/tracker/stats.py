import sys
from pympler.util.compat import pickle
from copy import deepcopy
from pympler.util.stringutils import trunc, pp, pp_timestamp

from pympler.asizeof import Asized

__all__ = ["Stats", "ConsoleStats", "HtmlStats"]


def _merge_asized(a, b, level=0):
    """
    Merge **Asized** instances `a` and `b` into `a`.
    """
    ref2key = lambda r: r.name.split(':')[0]
    a.size += b.size
    a.flat += b.flat
    if level > 0:
        a.name = ref2key(a)
    # Add refs from b to a. Any new refs are appended.
    a.refs = list(a.refs) # we may need to append items
    refs = {}
    for ref in a.refs:
        refs[ref2key(ref)] = ref
    for ref in b.refs:
        key = ref2key(ref)
        if key in refs:
            _merge_asized(refs[key], ref, level=level+1)
        else:
            # Don't modify existing Asized instances => deepcopy
            a.refs.append(deepcopy(ref))
            a.refs[-1].name = key

def _merge_objects(ts, merged, obj):
    """
    Merge the snapshot size information of multiple tracked objects.
    The tracked object `obj` is scanned for size information at time `ts`.
    The sizes are merged into **Asized** instance `merged`.
    """
    sz = None
    for (t, sized) in obj.footprint:
        if t == ts:
            sz = sized
    if sz:
        _merge_asized(merged, sized)


#
# Off-line Analysis
#

class Stats(object):
    """
    Presents the memory statisitics gathered by a `ClassTracker` based on user
    preferences.
    """

    def __init__(self, tracker=None, filename=None, stream=sys.stdout):
        """
        Initialize the data log structures either from a `ClassTracker` instance
        (argument `tracker`) or a previously dumped file (argument `filename`).
        """
        self.stream = stream
        self.tracker = tracker
        if tracker:
            self.index = tracker.index
            self.footprint = tracker.footprint
        else:
            self.index = None
            self.footprint = None
        self.sorted = []
        if filename:
            self.load_stats(filename)

    def load_stats(self, fdump):
        """
        Load the data from a dump file.
        The argument `fdump` can be either a filename or a an open file object
        that requires read access.
        """
        if isinstance(fdump, type('')):
            fdump = open(fdump, 'rb')
        self.index = pickle.load(fdump)
        self.footprint = pickle.load(fdump)
        self.sorted = []

    def dump_stats(self, fdump, close=1):
        """
        Dump the logged data to a file.
        The argument `file` can be either a filename or an open file object
        that requires write access. `close` controls if the file is closed
        before leaving this method (the default behaviour).
        """
        if self.tracker:
            self.tracker.stop_periodic_snapshots()

        if isinstance(fdump, type('')):
            fdump = open(fdump, 'wb')
        pickle.dump(self.index, fdump, protocol=pickle.HIGHEST_PROTOCOL)
        pickle.dump(self.footprint, fdump, protocol=pickle.HIGHEST_PROTOCOL)
        if close:
            fdump.close()

    def _init_sort(self):
        """
        Prepare the data to be sorted.
        If not yet sorted, import all tracked objects from the tracked index.
        Extend the tracking information by implicit information to make
        sorting easier (DSU pattern).
        """
        if not self.sorted:
            # Identify the snapshot that tracked the largest amount of memory.
            tmax = None
            maxsize = 0
            for fp in self.footprint:
                if fp.tracked_total > maxsize:
                    tmax = fp.timestamp
            for key in list(self.index.keys()):
                for to in self.index[key]:
                    to.classname = key
                    to.size = to.get_max_size()
                    to.tsize = to.get_size_at_time(tmax)
                self.sorted.extend(self.index[key])

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
        list which is used by `Stats.print_stats()` and other methods. The
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

        The function returns self to allow calling functions on the result::

            stats.sort_stats('size').reverse_order().print_stats()
        """

        criteria = ('classname', 'tsize', 'birth', 'death',
                    'name', 'repr', 'size')

        if not set(criteria).issuperset(set(args)):
            raise ValueError("Invalid sort criteria")

        if not args:
            args = criteria

        def _sort(a, b, crit=args):
            for c in crit:
                res = 0
                if getattr(a,c) < getattr(b,c):
                    res = -1
                elif getattr(a,c) > getattr(b,c):
                    res = 1
                if res:
                    if c in ('tsize', 'size', 'death'):
                        return -res
                    return res
            return 0

        def cmp2key(mycmp):
            "Converts a cmp= function into a key= function"
            class K:
                def __init__(self, obj, *args):
                    self.obj = obj
                #def __cmp__(self, other):
                #    return mycmp(self.obj, other.obj)
                def __lt__(self, other):
                    return mycmp(self.obj, other.obj) < 0
            return K

        if not self.sorted:
            self._init_sort()

        #self.sorted.sort(_sort)
        self.sorted.sort(key=cmp2key(_sort))

        return self

    def reverse_order(self):
        """
        Reverse the order of the tracked instance index `self.sorted`.
        """
        if not self.sorted:
            self._init_sort()
        self.sorted.reverse()
        return self

    def format_trace(trace):
        """
        Convert the (stripped) stack-trace to a nice readable format. The stack
        trace `trace` is a list of frame records as returned by
        **inspect.stack** but without the frame objects.
        Returns a string.
        """
        lines = []
        for fr in trace:
            for line in fr[3]:
                lines.append('    '+line.strip()+'\n')
            lines.append('  %s:%4d in %s\n' % (fr[0], f[1], f[2]))
        return ''.join(lines)

    def diff_stats(self, stats):
        return None # TODO

    def annotate_snapshot(self, snapshot):
        """
        Store additional statistical data in snapshot.
        """
        if hasattr(snapshot, 'classes'):
            return

        snapshot.classes = {}

        for classname in list(self.index.keys()):
            total = 0
            active = 0
            merged = Asized(0,0)
            for to in self.index[classname]:
                _merge_objects(snapshot.timestamp, merged, to)
                total += to.get_size_at_time(snapshot.timestamp)
                if to.birth < snapshot.timestamp and (to.death is None or
                   to.death > snapshot.timestamp):
                    active += 1
            try:
                pct = total * 100.0 / snapshot.asizeof_total
            except ZeroDivisionError:
                pct = 0
            try:
                avg = total / active
            except ZeroDivisionError:
                avg = 0

            snapshot.classes[classname] = {'sum': total, 'avg': avg, 'pct': pct, \
                'active': active}
            snapshot.classes[classname]['merged'] = merged


class ConsoleStats(Stats):

    def _print_refs(self, refs, total, prefix='    ', level=1, minsize=0, minpct=0.1):
        """
        Print individual referents recursively.
        """
        lrefs = list(refs)
        lrefs.sort(key=lambda x: x.size)
        lrefs.reverse()
        for r in lrefs:
            if r.size > minsize and (r.size*100.0/total) > minpct:
                self.stream.write('%-50s %-14s %3d%% [%d]\n' % (trunc(prefix+str(r.name),50),
                    pp(r.size),int(r.size*100.0/total), level))
                self._print_refs(r.refs, total, prefix=prefix+'  ', level=level+1)

    def print_object(self, to, full=0):
        """
        Print the gathered information of object `to` in human-readable format.
        """
        if full:
            if to.death:
                self.stream.write('%-32s ( free )   %-35s\n' % (
                    trunc(to.name, 32, left=1), trunc(to.repr, 35)))
            else:
                self.stream.write('%-32s 0x%08x %-35s\n' % (
                    trunc(to.name, 32, left=1), to.id, trunc(to.repr, 35)))
            try:
                self.stream.write(self.format_trace(to.trace))
            except AttributeError:
                pass
            for (ts, size) in to.footprint:
                self.stream.write('  %-30s %s\n' % (pp_timestamp(ts), pp(size.size)))
                self._print_refs(size.refs, size.size)
            if to.death is not None:
                self.stream.write('  %-30s finalize\n' % pp_timestamp(ts))
        else:
            # TODO Print size for largest snapshot (get_size_at_time)
            # Unused ATM: Maybe drop this type of reporting
            size = to.get_max_size()
            if to.repr:
                self.stream.write('%-64s %-14s\n' % (trunc(to.repr, 64), pp(size)))
            else:
                self.stream.write('%-64s %-14s\n' % (trunc(to.name, 64), pp(size)))

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
        if self.tracker:
            self.tracker.stop_periodic_snapshots()

        if not self.sorted:
            self.sort_stats()

        _sorted = self.sorted

        if filter:
            _sorted = [to for to in _sorted if filter in to.classname]

        if limit < 1.0:
            _sorted = _sorted[:int(len(self.sorted)*limit)+1]
        elif limit > 1:
            _sorted = _sorted[:int(limit)]

        # Emit per-instance data
        for to in _sorted:
            self.print_object(to, full=1)

    def print_summary(self):
        """
        Print per-class summary for each snapshot.
        """
        # Emit class summaries for each snapshot
        classlist = list(self.index.keys())
        classlist.sort()

        fobj = self.stream

        fobj.write('---- SUMMARY '+'-'*66+'\n')
        for fp in self.footprint:
            self.annotate_snapshot(fp)
            fobj.write('%-35s %11s %12s %12s %5s\n' % \
                (trunc(fp.desc, 35), 'active', pp(fp.asizeof_total),
                 'average', 'pct'))
            for classname in classlist:
                try:
                    info = fp.classes[classname]
                except KeyError:
                    # No such class in this snapshot, if print_stats is called
                    # multiple times there may exist older annotations in
                    # earlier snapshots.
                    pass
                else:
                    total, avg, pct, active = info['sum'], info['avg'], info['pct'], info['active']
                    fobj.write('  %-33s %11d %12s %12s %4d%%\n' % \
                        (trunc(classname, 33), active, pp(total), pp(avg), pct))
        fobj.write('-'*79+'\n')

class HtmlStats(Stats):
    """
    Output the `ClassTracker` statistics as HTML pages and graphs.
    """

    style          = """<style type="text/css">
        table { width:100%; border:1px solid #000; border-spacing:0px; }
        td, th { border:0px; }
        div { width:200px; padding:10px; background-color:#FFEECC; }
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

    nopylab_msg    = """<div color="#FFCCCC">Could not generate %s chart!
    Install <a href="http://matplotlib.sourceforge.net/">Matplotlib</a>
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

    def _print_refs(self, fobj, refs, total, level=1, minsize=0, minpct=0.1):
        """
        Print individual referents recursively.
        """
        lrefs = list(refs)
        lrefs.sort(key=lambda x: x.size)
        lrefs.reverse()
        if level == 1:
            fobj.write('<table>\n')
        for r in lrefs:
            if r.size > minsize and (r.size*100.0/total) > minpct:
                data = {'level': level, 'name': trunc(str(r.name),128),
                    'size': pp(r.size), 'pct': r.size*100.0/total }
                fobj.write(self.refrow % data)
                self._print_refs(fobj, r.refs, total, level=level+1)
        if level == 1:
            fobj.write("</table>\n")

    class_summary = """<p>%(cnt)d instances of %(cls)s were registered. The
    average size is %(avg)s, the minimal size is %(min)s, the maximum size is
    %(max)s.</p>\n"""
    class_snapshot = '''<h3>Snapshot: %(name)s, %(total)s occupied by instances of
    class %(cls)s</h3>\n'''

    def print_class_details(self, fname, classname):
        """
        Print detailed statistics and instances for the class `classname`. All
        data will be written to the file `fname`.
        """
        fobj = open(fname, "w")
        fobj.write(self.header % (classname, self.style))

        fobj.write("<h1>%s</h1>\n" % (classname))

        sizes = [to.get_max_size() for to in self.index[classname]]
        total = 0
        for s in sizes:
            total += s
        data = {'cnt': len(self.index[classname]), 'cls': classname}
        data['avg'] = pp(total / len(sizes))
        data['max'] = pp(max(sizes))
        data['min'] = pp(min(sizes))
        fobj.write(self.class_summary % data)

        fobj.write(self.charts[classname])

        fobj.write("<h2>Coalesced Referents per Snapshot</h2>\n")
        for fp in self.footprint:
            if classname in fp.classes:
                merged = fp.classes[classname]['merged']
                fobj.write(self.class_snapshot % {
                    'name': fp.desc, 'cls':classname, 'total': pp(merged.size)
                })
                if merged.refs:
                    self._print_refs(fobj, merged.refs, merged.size)
                else:
                    fobj.write('<p>No per-referent sizes recorded.</p>\n')

        fobj.write("<h2>Instances</h2>\n")
        for to in self.index[classname]:
            fobj.write('<table id="tl" width="100%" rules="rows">\n')
            fobj.write('<tr><td id="hl" width="140px">Instance</td><td id="hl">%s at 0x%08x</td></tr>\n' % (to.name, to.id))
            if to.repr:
                fobj.write("<tr><td>Representation</td><td>%s&nbsp;</td></tr>\n" % to.repr)
            fobj.write("<tr><td>Lifetime</td><td>%s - %s</td></tr>\n" % (pp_timestamp(to.birth), pp_timestamp(to.death)))
            if hasattr(to, 'trace'):
                trace = "<pre>%s</pre>" % (self.format_trace(to.trace))
                fobj.write("<tr><td>Instantiation</td><td>%s</td></tr>\n" % trace)
            for (ts, size) in to.footprint:
                fobj.write("<tr><td>%s</td>" % pp_timestamp(ts))
                if not size.refs:
                    fobj.write("<td>%s</td></tr>\n" % pp(size.size))
                else:
                    fobj.write("<td>%s" % pp(size.size))
                    self._print_refs(fobj, size.refs, size.size)
                    fobj.write("</td></tr>\n")
            fobj.write("</table>\n")

        fobj.write(self.footer)
        fobj.close()

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
        ClassTracker tracked %(tracked)s in total. The measurable objects
        including code objects but excluding overhead have a total size of
        %(asizeof)s.</p>\n"""

    def create_title_page(self, filename, title=''):
        """
        Output the title page.
        """
        fobj = open(filename, "w")
        fobj.write(self.header % (title, self.style))

        fobj.write("<h1>%s</h1>\n" % title)
        fobj.write("<h2>Memory distribution over time</h2>\n")
        fobj.write(self.charts['snapshots'])

        fobj.write("<h2>Snapshots statistics</h2>\n")
        fobj.write('<table id="nb">\n')

        classlist = list(self.index.keys())
        classlist.sort()

        for fp in self.footprint:
            fobj.write('<tr><td>\n')
            fobj.write('<table id="tl" rules="rows">\n')
            fobj.write("<h3>%s snapshot at %s</h3>\n" % (fp.desc or 'Untitled',\
                pp_timestamp(fp.timestamp)))

            data = {}
            data['sys']      = pp(fp.system_total.vsz)
            data['tracked']  = pp(fp.tracked_total)
            data['asizeof']  = pp(fp.asizeof_total)
            data['overhead'] = pp(getattr(fp, 'overhead', 0))

            fobj.write(self.snapshot_summary % data)

            if fp.tracked_total:
                fobj.write(self.snapshot_cls_header)
                for classname in classlist:
                    data = fp.classes[classname].copy()
                    data['cls'] = "<a href='%s'>%s</a>" % (self.links[classname], classname)
                    data['sum'] = pp(data['sum'])
                    data['avg'] = pp(data['avg'])
                    fobj.write(self.snapshot_cls % data)
            fobj.write('</table>')
            fobj.write('</td><td>\n')
            if fp.tracked_total:
                fobj.write(self.charts[fp])
            fobj.write('</td></tr>\n')

        fobj.write("</table>\n")
        fobj.write(self.footer)
        fobj.close()

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
        for to in self.index[classname]:
            cnt.append([to.birth, 1])
            if to.death:
                cnt.append([to.death, -1])
        cnt.sort()
        for i in range(1, len(cnt)):
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

        classlist = list(self.index.keys())
        classlist.sort()

        x = [fp.timestamp for fp in self.footprint]
        base = [0] * len(self.footprint)
        poly_labels = []
        polys = []
        for cn in classlist:
            pct = [fp.classes[cn]['pct'] for fp in self.footprint]
            if max(pct) > 3.0:
                sz = [float(fp.classes[cn]['sum'])/(1024*1024) for fp in self.footprint]
                sz = list(map( lambda x, y: x+y, base, sz ))
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
            from pylab import figure, title, pie, axes, savefig
            from pylab import sum as pylab_sum
        except ImportError:
            return self.nopylab_msg % ("pie_chart")

        # Don't bother illustrating a pie without pieces.
        if not snapshot.tracked_total:
            return ''

        classlist = []
        sizelist = []
        for k, v in list(snapshot.classes.items()):
            if v['pct'] > 3.0:
                classlist.append(k)
                sizelist.append(v['sum'])
        sizelist.insert(0, snapshot.asizeof_total - pylab_sum(sizelist))
        classlist.insert(0, 'Other')
        #sizelist = [x*0.01 for x in sizelist]

        title("Snapshot (%s) Memory Distribution" % (snapshot.desc))
        figure(figsize=(8,8))
        axes([0.1, 0.1, 0.8, 0.8])
        pie(sizelist, labels=classlist)
        savefig(filename, dpi=50)

        return self.chart_tag % (filename)

    def create_html(self, fname, title="ClassTracker Statistics"):
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

        # Annotate all snapshots in advance
        for fp in self.footprint:
            self.annotate_snapshot(fp)

        # Create charts. The tags to show the images are returned and stored in
        # the self.charts dictionary. This allows to return alternative text if
        # the chart creation framework is not available.
        self.charts = {}
        fn = path.join(self.filesdir, 'timespace.png')
        self.charts['snapshots'] = self.create_snapshot_chart(fn)

        for fp, idx in zip(self.footprint, list(range(len(self.footprint)))):
            fn = path.join(self.filesdir, 'fp%d.png' % (idx))
            self.charts[fp] = self.create_pie_chart(fp, fn)

        for cn in list(self.index.keys()):
            fn = path.join(self.filesdir, cn.replace('.', '_')+'-lt.png')
            self.charts[cn] = self.create_lifetime_chart(cn, fn)

        # Create HTML pages first for each class and then the index page.
        for cn in list(self.index.keys()):
            fn = path.join(self.filesdir, cn.replace('.', '_')+'.html')
            self.links[cn]  = fn
            self.print_class_details(fn, cn)

        self.create_title_page(fname, title=title)
