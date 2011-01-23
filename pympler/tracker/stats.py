"""
Provide saving, loading and presenting gathered `ClassTracker` statistics.
"""

import os
import sys
from pympler.util.compat import pickle
from copy import deepcopy
from pympler.util.stringutils import trunc, pp, pp_timestamp

from pympler.asizeof import Asized

__all__ = ["Stats", "ConsoleStats", "HtmlStats"]


def _merge_asized(base, other, level=0):
    """
    Merge **Asized** instances `base` and `other` into `base`.
    """
    ref2key = lambda ref: ref.name.split(':')[0]
    base.size += other.size
    base.flat += other.flat
    if level > 0:
        base.name = ref2key(base)
    # Add refs from other to base. Any new refs are appended.
    base.refs = list(base.refs) # we may need to append items
    refs = {}
    for ref in base.refs:
        refs[ref2key(ref)] = ref
    for ref in other.refs:
        key = ref2key(ref)
        if key in refs:
            _merge_asized(refs[key], ref, level=level+1)
        else:
            # Don't modify existing Asized instances => deepcopy
            base.refs.append(deepcopy(ref))
            base.refs[-1].name = key


def _merge_objects(tref, merged, obj):
    """
    Merge the snapshot size information of multiple tracked objects.  The
    tracked object `obj` is scanned for size information at time `tref`.
    The sizes are merged into **Asized** instance `merged`.
    """
    size = None
    for (timestamp, tsize) in obj.footprint:
        if timestamp == tref:
            size = tsize
    if size:
        _merge_asized(merged, size)


def _format_trace(trace):
    """
    Convert the (stripped) stack-trace to a nice readable format. The stack
    trace `trace` is a list of frame records as returned by
    **inspect.stack** but without the frame objects.
    Returns a string.
    """
    lines = []
    for frm in trace:
        for line in frm[3]:
            lines.append('    '+line.strip()+'\n')
        lines.append('  %s:%4d in %s\n' % (frm[0], frm[1], frm[2]))
    return ''.join(lines)


class Stats(object):
    """
    Presents the memory statistics gathered by a `ClassTracker` based on user
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
        The argument `fdump` can be either a filename or an open file object
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
            for footprint in self.footprint:
                if footprint.tracked_total > maxsize:
                    tmax = footprint.timestamp
            for key in list(self.index.keys()):
                for tobj in self.index[key]:
                    tobj.classname = key
                    tobj.size = tobj.get_max_size()
                    tobj.tsize = tobj.get_size_at_time(tmax)
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

        def _sort(to1, to2, crit=args):
            """Compare two objects using a list of attributes."""
            for attr in crit:
                toa = getattr(to1, attr)
                tob = getattr(to2, attr)
                res = (toa > tob) - (toa < tob)
                if res != 0:
                    if attr in ('tsize', 'size', 'death'):
                        return -res
                    return res
            return 0

        def cmp2key(mycmp):
            """Converts a cmp= function into a key= function"""
            class ObjectWrapper(object):
                """Wraps an object exposing the given comparison logic."""
                def __init__(self, obj, *args):
                    self.obj = obj
                def __lt__(self, other):
                    return mycmp(self.obj, other.obj) < 0
            return ObjectWrapper

        if not self.sorted:
            self._init_sort()

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
            merged = Asized(0, 0)
            for tobj in self.index[classname]:
                _merge_objects(snapshot.timestamp, merged, tobj)
                total += tobj.get_size_at_time(snapshot.timestamp)
                if tobj.birth < snapshot.timestamp and \
                    (tobj.death is None or tobj.death > snapshot.timestamp):
                    active += 1
            try:
                pct = total * 100.0 / snapshot.asizeof_total
            except ZeroDivisionError:
                pct = 0
            try:
                avg = total / active
            except ZeroDivisionError:
                avg = 0

            snapshot.classes[classname] = dict(sum=total,
                                               avg=avg,
                                               pct=pct,
                                               active=active)
            snapshot.classes[classname]['merged'] = merged


class ConsoleStats(Stats):
    """
    Presentation layer for `Stats` to be used in text-based consoles.
    """

    def _print_refs(self, refs, total, prefix='    ',
                    level=1, minsize=0, minpct=0.1):
        """
        Print individual referents recursively.
        """
        lrefs = list(refs)
        lrefs.sort(key=lambda x: x.size)
        lrefs.reverse()
        for ref in lrefs:
            if ref.size > minsize and (ref.size*100.0/total) > minpct:
                self.stream.write('%-50s %-14s %3d%% [%d]\n' % (
                    trunc(prefix+str(ref.name), 50),
                    pp(ref.size),
                    int(ref.size*100.0/total),
                    level
                ))
                self._print_refs(ref.refs, total, prefix=prefix+'  ',
                                 level=level+1)


    def print_object(self, tobj, full=0):
        """
        Print the gathered information of object `tobj` in human-readable format.
        """
        if full:
            if tobj.death:
                self.stream.write('%-32s ( free )   %-35s\n' % (
                    trunc(tobj.name, 32, left=1), trunc(tobj.repr, 35)))
            else:
                self.stream.write('%-32s 0x%08x %-35s\n' % (
                    trunc(tobj.name, 32, left=1),
                    tobj.id,
                    trunc(tobj.repr, 35)
                ))
            if tobj.trace:
                self.stream.write(_format_trace(tobj.trace))
            for (timestamp, size) in tobj.footprint:
                self.stream.write('  %-30s %s\n' % (
                    pp_timestamp(timestamp), pp(size.size)
                ))
                self._print_refs(size.refs, size.size)
            if tobj.death is not None:
                self.stream.write('  %-30s finalize\n' % (
                    pp_timestamp(tobj.death),
                ))
        else:
            size = tobj.get_max_size()
            if tobj.repr:
                self.stream.write('%-64s %-14s\n' % (
                    trunc(tobj.repr, 64),
                    pp(size)
                ))
            else:
                self.stream.write('%-64s %-14s\n' % (
                    trunc(tobj.name, 64),
                    pp(size)
                ))


    def print_stats(self, clsname=None, limit=1.0):
        """
        Write tracked objects to stdout.  The output can be filtered and pruned.
        Only objects are printed whose classname contain the substring supplied
        by the `clsname` argument.  The output can be pruned by passing a limit
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

        if clsname:
            _sorted = [to for to in _sorted if clsname in to.classname]

        if limit < 1.0:
            _sorted = _sorted[:int(len(self.sorted)*limit)+1]
        elif limit > 1:
            _sorted = _sorted[:int(limit)]

        # Emit per-instance data
        for tobj in _sorted:
            self.print_object(tobj, full=1)


    def print_summary(self):
        """
        Print per-class summary for each snapshot.
        """
        # Emit class summaries for each snapshot
        classlist = list(self.index.keys())
        classlist.sort()

        fobj = self.stream

        fobj.write('---- SUMMARY '+'-'*66+'\n')
        for footprint in self.footprint:
            self.annotate_snapshot(footprint)
            fobj.write('%-35s %11s %12s %12s %5s\n' % (
                trunc(footprint.desc, 35),
                'active',
                pp(footprint.asizeof_total),
                'average',
                'pct'
            ))
            for classname in classlist:
                info = footprint.classes.get(classname)
                # If 'info' is None there is no such class in this snapshot. If
                # print_stats is called multiple times there may exist older
                # annotations in earlier snapshots.
                if info:
                    fobj.write('  %-33s %11d %12s %12s %4d%%\n' % (
                        trunc(classname, 33),
                        info['active'],
                        pp(info['sum']),
                        pp(info['avg']),
                        info['pct']
                    ))
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
        for ref in lrefs:
            if ref.size > minsize and (ref.size*100.0/total) > minpct:
                data = dict(level=level,
                            name=trunc(str(ref.name), 128),
                            size=pp(ref.size),
                            pct=ref.size*100.0/total)
                fobj.write(self.refrow % data)
                self._print_refs(fobj, ref.refs, total, level=level+1)
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

        sizes = [tobj.get_max_size() for tobj in self.index[classname]]
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
        for footprint in self.footprint:
            if classname in footprint.classes:
                merged = footprint.classes[classname]['merged']
                fobj.write(self.class_snapshot % {
                    'name': footprint.desc, 'cls':classname, 'total': pp(merged.size)
                })
                if merged.refs:
                    self._print_refs(fobj, merged.refs, merged.size)
                else:
                    fobj.write('<p>No per-referent sizes recorded.</p>\n')

        fobj.write("<h2>Instances</h2>\n")
        for tobj in self.index[classname]:
            fobj.write('<table id="tl" width="100%" rules="rows">\n')
            fobj.write('<tr><td id="hl" width="140px">Instance</td><td id="hl">%s at 0x%08x</td></tr>\n' % (tobj.name, tobj.id))
            if tobj.repr:
                fobj.write("<tr><td>Representation</td><td>%s&nbsp;</td></tr>\n" % tobj.repr)
            fobj.write("<tr><td>Lifetime</td><td>%s - %s</td></tr>\n" % (pp_timestamp(tobj.birth), pp_timestamp(tobj.death)))
            if tobj.trace:
                trace = "<pre>%s</pre>" % (_format_trace(tobj.trace))
                fobj.write("<tr><td>Instantiation</td><td>%s</td></tr>\n" % trace)
            for (timestamp, size) in tobj.footprint:
                fobj.write("<tr><td>%s</td>" % pp_timestamp(timestamp))
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

    def relative_path(self, filepath, basepath=None):
        """
        Convert the filepath path to a relative path against basepath. By
        default basepath is self.basedir.
        """
        if basepath is None:
            basepath = self.basedir
        if not basepath:
            return filepath
        if filepath.startswith(basepath):
            rel = filepath[len(basepath):]
        if rel and rel[0] == os.sep:
            rel = rel[1:]
        return rel

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

        for footprint in self.footprint:
            fobj.write('<tr><td>\n')
            fobj.write('<table id="tl" rules="rows">\n')
            fobj.write("<h3>%s snapshot at %s</h3>\n" % (
                footprint.desc or 'Untitled',
                pp_timestamp(footprint.timestamp)
            ))

            data = {}
            data['sys']      = pp(footprint.system_total.vsz)
            data['tracked']  = pp(footprint.tracked_total)
            data['asizeof']  = pp(footprint.asizeof_total)
            data['overhead'] = pp(getattr(footprint, 'overhead', 0))

            fobj.write(self.snapshot_summary % data)

            if footprint.tracked_total:
                fobj.write(self.snapshot_cls_header)
                for classname in classlist:
                    data = footprint.classes[classname].copy()
                    data['cls'] = '<a href="%s">%s</a>' % (self.relative_path(self.links[classname]), classname)
                    data['sum'] = pp(data['sum'])
                    data['avg'] = pp(data['avg'])
                    fobj.write(self.snapshot_cls % data)
            fobj.write('</table>')
            fobj.write('</td><td>\n')
            if footprint.tracked_total:
                fobj.write(self.charts[footprint])
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
        for tobj in self.index[classname]:
            cnt.append([tobj.birth, 1])
            if tobj.death:
                cnt.append([tobj.death, -1])
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

        return self.chart_tag % (os.path.basename(filename))

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

        times = [footprint.timestamp for footprint in self.footprint]
        base = [0] * len(self.footprint)
        poly_labels = []
        polys = []
        for cn in classlist:
            pct = [footprint.classes[cn]['pct'] for footprint in self.footprint]
            if max(pct) > 3.0:
                sz = [float(fp.classes[cn]['sum'])/(1024*1024) for fp in self.footprint]
                sz = [sx+sy for sx, sy in zip(base, sz)]
                xp, yp = mlab.poly_between(times, base, sz)
                polys.append( ((xp, yp), {'label': cn}) )
                poly_labels.append(cn)
                base = sz

        figure()
        title("Snapshot Memory")
        xlabel("Execution Time [s]")
        ylabel("Virtual Memory [MiB]")

        sizes = [float(fp.asizeof_total)/(1024*1024) for fp in self.footprint]
        plot(times, sizes, 'r--', label='Total')
        sizes = [float(fp.tracked_total)/(1024*1024) for fp in self.footprint]
        plot(times, sizes, 'b--', label='Tracked total')

        for (args, kwds) in polys:
            fill(*args, **kwds)
        legend(loc=2)
        savefig(filename)

        return self.chart_tag % (self.relative_path(filename))

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

        return self.chart_tag % (self.relative_path(filename))

    def create_html(self, fname, title="ClassTracker Statistics"):
        """
        Create HTML page `fname` and additional files in a directory derived
        from `fname`.
        """
        # Create a folder to store the charts and additional HTML files.
        self.basedir = os.path.dirname(os.path.abspath(fname))
        self.filesdir = os.path.splitext(fname)[0] + '_files'
        if not os.path.isdir(self.filesdir):
            os.mkdir(self.filesdir)
        self.filesdir = os.path.abspath(self.filesdir)
        self.links = {}

        # Annotate all snapshots in advance
        for footprint in self.footprint:
            self.annotate_snapshot(footprint)

        # Create charts. The tags to show the images are returned and stored in
        # the self.charts dictionary. This allows to return alternative text if
        # the chart creation framework is not available.
        self.charts = {}
        fn = os.path.join(self.filesdir, 'timespace.png')
        self.charts['snapshots'] = self.create_snapshot_chart(fn)

        for fp, idx in zip(self.footprint, list(range(len(self.footprint)))):
            fn = os.path.join(self.filesdir, 'fp%d.png' % (idx))
            self.charts[fp] = self.create_pie_chart(fp, fn)

        for cn in list(self.index.keys()):
            fn = os.path.join(self.filesdir, cn.replace('.', '_')+'-lt.png')
            self.charts[cn] = self.create_lifetime_chart(cn, fn)

        # Create HTML pages first for each class and then the index page.
        for cn in list(self.index.keys()):
            fn = os.path.join(self.filesdir, cn.replace('.', '_')+'.html')
            self.links[cn]  = fn
            self.print_class_details(fn, cn)

        self.create_title_page(fname, title=title)
