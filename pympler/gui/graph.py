"""
This module exposes utilities to illustrate objects and their references as
(directed) graphs. The current implementation requires 'graphviz' to be
installed.
"""

from pympler.asizeof import Asizer, _inst_refs
from pympler.util.stringutils import safe_repr, trunc
from pympler.util.compat import encode4pipe
from gc import get_referents
from inspect import getmembers
from subprocess import Popen, PIPE
from copy import copy
from sys import platform

__all__ = ['ReferenceGraph']


# Popen might lead to deadlocks when file descriptors are leaked to
# sub-processes on Linux. On Windows, however, close_fds=True leads to
# ValueError if stdin/stdout/stderr is piped:
# http://code.google.com/p/pympler/issues/detail?id=28#c1
popen_flags = {}
if platform not in ['win32']:
    popen_flags['close_fds'] = True


class _MetaObject(object):
    """
    The _MetaObject stores meta-information, like a string representation,
    corresponding to each object passed to a ReferenceGraph.
    """
    __slots__ = ('size', 'id', 'type', 'str', 'group')


class _Edge(object):
    """
    Describes a reference from one object `src` to another object `dst`.
    """
    __slots__ = ('src', 'dst', 'label', 'group')

    def __init__(self, src, dst, label):
        self.src = src
        self.dst = dst
        self.label = label
        self.group = None

    def __repr__(self):
        return "<%08x => %08x, '%s', %s>" % (self.src, self.dst, self.label, self.group)

    def __hash__(self):
        return (self.src, self.dst, self.label).__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class ReferenceGraph(object):
    """
    The ReferenceGraph illustrates the references between a collection of objects
    by rendering a directed graph. That requires that 'graphviz' is installed.

    >>> from pympler.gui.graph import ReferenceGraph
    >>> a = 42
    >>> b = 'spam'
    >>> c = {a: b}
    >>> gb = ReferenceGraph([a,b,c])
    >>> gb.render('spam.eps')
    True
    """
    def __init__(self, objects, reduce=False):
        """
        Initialize the ReferenceGraph with a collection of `objects`.
        """
        self.objects = list(objects)
        self.count = len(self.objects)
        self.objects_in_cycles = None

        if reduce:
            self.count_in_cycles = self._reduce_to_cycles()

        self._get_edges()
        self._annotate_objects()


    def _eliminate_leafs(self, graph):
        """
        Eliminate leaf objects - that are objects not referencing any other
        objects in the list `graph`. Returns the list of objects without the
        objects identified as leafs.
        """
        result = []
        idset = set([id(x) for x in graph])
        for n in graph:
            refset = set([id(x) for x in get_referents(n)])
            if refset.intersection(idset):
                result.append(n)
        return result


    def _reduce_to_cycles(self):
        """
        Iteratively eliminate leafs to reduce the set of objects to only those
        that build cycles. Return the number of objects involved in reference
        cycles. If there are no cycles, `self.objects` will be an empty list and
        this method returns 0.
        """
        cycles = self.objects[:]
        cnt = 0
        while cnt != len(cycles):
            cnt = len(cycles)
            cycles = self._eliminate_leafs(cycles)
        self.objects = cycles
        return len(self.objects)


    def _get_edges(self):
        """
        Compute the edges for the reference graph.
        The function returns a set of tuples (id(a), id(b), ref) if a
        references b with the referent 'ref'.
        """
        idset = set([id(x) for x in self.objects])
        self.edges = set([])
        for n in self.objects:
            refset = set([id(x) for x in get_referents(n)])
            for ref in refset.intersection(idset):
                label = ''
                members = None
                if isinstance(n, dict):
                    members = n.items()
                if not members:
                    members = getmembers(n)
                for (k, v) in members:
                    if id(v) == ref:
                        label = k
                        break
                if not label:
                    # Try to use asizeof's referent generator to identify
                    # referents of old-style classes.
                    try:
                        if type(n).__name__ == 'instance':
                            for member in _inst_refs(n, 1):
                                if id(member.ref) == ref:
                                    label = member.name
                    except AttributeError:
                        pass
                self.edges.add(_Edge(id(n), ref, label))


    def _annotate_groups(self):
        """
        Annotate the objects belonging to separate (non-connected) graphs with
        individual indices.
        """
        g = {}
        for x in self.metadata:
            g[x.id] = x

        idx = 0
        for x in self.metadata:
            if not hasattr(x, 'group'):
                x.group = idx
                idx += 1
            neighbors = set()
            for e in self.edges:
                if e.src == x.id:
                    neighbors.add(e.dst)
                if e.dst == x.id:
                    neighbors.add(e.src)
            for nb in neighbors:
                g[nb].group = min(x.group, getattr(g[nb], 'group', idx))

        # Assign the edges to the respective groups. Both "ends" of the edge
        # should share the same group so just use the first object's group.
        for e in self.edges:
            e.group = g[e.src].group

        self._max_group = idx


    def _filter_group(self, group):
        """
        Eliminate all objects but those which belong to `group`. Only
        ``self.metadata`` and ``self.edges`` are modified.
        Returns `True` if the group is non-empty. Otherwise returns `False`.
        """
        self.metadata = [x for x in self.metadata if x.group == group]
        self.count = len(self.metadata)
        if self.metadata == []:
            return False

        self.edges = [e for e in self.edges if e.group == group]

        del self._max_group

        return True


    def split(self):
        """
        Split the graph into sub-graphs. Only connected objects belong to the
        same graph. `split` yields copies of the Graph object. Shallow copies
        are used that only replicate the meta-information, but share the same
        object list ``self.objects``.

        >>> from pympler.gui.graph import ReferenceGraph
        >>> a = 42
        >>> b = 'spam'
        >>> c = {a: b}
        >>> t = (1,2,3)
        >>> rg = ReferenceGraph([a,b,c,t])
        >>> for subgraph in rg.split():
        ...   print subgraph.index
        0
        1
        """
        self._annotate_groups()
        index = 0

        for group in range(self._max_group):
            subgraph = copy(self)
            subgraph.metadata = self.metadata[:]
            subgraph.edges = self.edges.copy()

            if subgraph._filter_group(group):
                subgraph.index = index
                index += 1
                yield subgraph


    def _annotate_objects(self):
        """
        Extract meta-data describing the stored objects.
        """
        self.metadata = []
        sizer = Asizer()
        sizes = sizer.asizesof(*self.objects)
        self.total_size = sizer.total
        for obj, sz in map( lambda x, y: (x, y), self.objects, sizes ):
            md = _MetaObject()
            md.size = sz
            md.id = id(obj)
            try:
                md.type = obj.__class__.__name__
            except (AttributeError, ReferenceError):
                md.type = type(obj)
            try:
                md.str = safe_repr(obj, clip=128)
            except ReferenceError:
                md.str = ''
            self.metadata.append(md)


    def _get_graphviz_data(self):
        """
        Emit a graph representing the connections between the objects described
        within the metadata list. The text representation can be transformed to
        a graph with graphviz. Returns a string.
        """
        s = []
        header = '// Process this file with graphviz\n'
        s.append( header)
        s.append('digraph G {\n')
        s.append('    node [shape=box];\n')
        for md in self.metadata:
            label = trunc(md.str, 48).replace('"', "'")
            extra = ''
            if md.type == 'instancemethod':
                extra = ', color=red'
            elif md.type == 'frame':
                extra = ', color=orange'
            s.append('    "X%s" [ label = "%s\\n%s" %s ];\n' % \
                (hex(md.id)[1:], label, md.type, extra))
        for e in self.edges:
            extra = ''
            if e.label == '__dict__':
                extra = ',weight=100'
            s.append('    X%s -> X%s [label="%s"%s];\n' % \
                (hex(e.src)[1:], hex(e.dst)[1:], e.label, extra))

        s.append('}\n')
        return "".join(s)


    def render(self, filename, cmd='dot', format='ps', unflatten=False):
        """
        Render the graph to `filename` using graphviz. The graphviz invocation
        command may be overriden by specifying `cmd`. The `format` may be any
        specifier recognized by the graph renderer ('-Txxx' command).  The graph
        can be preprocessed by the *unflatten* tool if the `unflatten` parameter
        is True.  If there are no objects to illustrate, the method does not
        invoke graphviz and returns False. If the renderer returns successfully
        (return code 0), True is returned.

        An `OSError` is raised if the graphviz tool cannot be found.
        """
        if self.objects == []:
            return False

        data = self._get_graphviz_data()

        if unflatten:
            p1 = Popen(('unflatten', '-l7'), stdin=PIPE, stdout=PIPE,
                **popen_flags)
            p2 = Popen((cmd, '-T%s' % format, '-o', filename), stdin=p1.stdout,
                **popen_flags)
            p1.communicate(encode4pipe(data))
            p2.communicate()
            return p2.returncode == 0
        else:
            p = Popen((cmd, '-T%s' % format, '-o', filename), stdin=PIPE,
                **popen_flags)
            p.communicate(encode4pipe(data))
            return p.returncode == 0


    def write_graph(self, filename):
        """
        Write raw graph data which can be post-processed using graphviz.
        """
        f = open(filename, 'w')
        f.write(self._get_graphviz_data())
        f.close()

