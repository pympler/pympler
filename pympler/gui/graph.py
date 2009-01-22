"""
This module exposes utilities to illustrate objects and their references as
(directed) graphs. The current implementation requires 'graphviz' to be
installed.
"""

from pympler.asizeof import Asizer, _inst_refs
from pympler.util.stringutils import trunc, pp
from gc import get_referents
from inspect import getmembers
from subprocess import Popen, PIPE

__all__ = ['ReferenceGraph']

class _MetaObject(object):
    """
    The _MetaObject stores meta-information, like a string representation,
    corresponding to each object passed to a ReferenceGraph.
    """
    __slots__ = ('size', 'id', 'type', 'str')


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
                self.edges.add((id(n), ref, label))


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
                md.str = trunc(str(obj), 128)
            except ReferenceError:
                md.str = ''
            self.metadata.append(md)


    def _emit_graphviz_data(self, fobj):
        """
        Emit a graph representing the connections between the objects described
        within the metadata list. The text representation can be transformed to
        a graph with graphviz. The `fobj` parameter can either be an open file
        or a pipe to a process.  The file object has to permit write access and
        is closed at the end of the function.
        """
        header = '// Process this file with graphviz\n'
        fobj.write(header)
        fobj.write('digraph G {\n')
        for md in self.metadata:
            label = trunc(md.str, 48).replace('"', "'")
            extra = ''
            if md.type == 'instancemethod':
                extra = ', color=red'
            elif md.type == 'frame':
                extra = ', color=orange'
            fobj.write('    "X%08x" [ label = "%s\\n%s" %s ];\n' % \
                (md.id, label, md.type, extra))
        for (i, j, l) in self.edges:
            fobj.write('    X%08x -> X%08x [label="%s"];\n' % (i, j, l))

        fobj.write('}\n')
        fobj.close()


    def render(self, filename, cmd='dot', format='ps'):
        """
        Render the graph to `filename` using graphviz. The graphviz invocation
        command may be overriden by specifying `cmd`. The `format` may be any
        specifier recognized by the graph renderer ('-Txxx' command). If there
        are no objects to illustrate, the method does not invoke graphviz and
        returns False. If the renderer returns successfully (return code 0),
        True is returned.
        """
        if self.objects == []:
            return False

        p = Popen((cmd, '-T%s' % format, '-o', filename), stdin=PIPE)
        self._emit_graphviz_data(p.stdin)
        p.communicate()
        return p.returncode == 0


    def write_graph(self, filename):
        """
        Write raw graph data which can be post-processed using graphviz.
        """
        self._emit_graphviz_data(open(filename, 'w'))

