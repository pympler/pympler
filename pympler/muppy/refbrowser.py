"""Tree-like exploration of object referrers.

This module provides a base implementation for tree-like referrers browsing.
The two non-interactive classes ConsoleBrowser and FileBrowser output a tree
to the console or a file. Further types can be subclassed.

All types share a similar initialisation. That is, you provide a root object
and may specify further settings such as the initial depth of the tree or an
output function.
Afterwards you can print the tree which will be arranged based on your previous
settings.
"""
import gc
import inspect
import sys

import summary

class _Node(object):
    """A node as it is used in the tree structure.

    Each node contains the object it represents and a list of children.
    Children can be other nodes or arbitrary other objects. Any object
    in a tree which is not of the type _Node is considered a leaf.
    
    """
    def __init__(self, o, str_func=None):
        """You have to define the object this node represents. Also you can
        define an output function which will be used to represent this node.
        If no function is defined, the default str representation is used.

        keyword arguments
        str_func -- output function

        """
        self.o = o
        self.children = []
        self.str_func = str_func

    def __str__(self):
        """Override str(self.o) if str_func is defined."""
        if self.str_func is not None:
            return self.str_func(self.o)
        else:
            return str(self.o)

class RefBrowser(object):
    """Base class to other RefBrowser implementations.

    This base class provides means to extract a tree from a given root object
    and holds information on already known objects (to avoid repetition
    if requested).
    
    """

    def __init__(self, rootobject, maxdepth=3, str_func=summary._repr, repeat=True):
        """You have to provide the root object used in the refbrowser. 
        
        keyword arguments
        maxdepth -- maximum depth of the initial tree
        str_func -- function used when calling str(node)
        repeat -- should nodes appear repeatedly in the tree, or should be
                  referred to existing nodes

        """        
        self.root = rootobject
        self.maxdepth = maxdepth
        self.str_func = str_func
        self.repeat = repeat
        # objects which should be ignored while building the tree
        # e.g. the current frame
        self.ignore = []
        # set of object ids which are already included
        self.already_included = set()
        self.ignore.append(self.already_included)

    def get_tree(self):
        """Get a tree of referrers of the root object."""
        self.ignore.append(inspect.currentframe())
        return self._get_tree(self.root, self.maxdepth)
    
    def _get_tree(self, root, maxdepth):
        """Workhorse of the get_tree implementation.

        This is an recursive method which is why we have a wrapper method.
        root is the current root object of the tree which should be returned.
        Note that root is not of the type _Node.
        maxdepth defines how much further down the from the root the tree
        should be build.

        """
        self.ignore.append(inspect.currentframe())
        res = _Node(root, self.str_func) #PYCHOK use root parameter
        self.already_included.add(id(root)) #PYCHOK use root parameter
        if maxdepth == 0:
            return res
        objects = gc.get_referrers(root) #PYCHOK use root parameter
        self.ignore.append(objects)
        for o in objects:
            # XXX: find a better way to ignore dict of _Node objects
            if isinstance(o, dict):
                sampleNode = _Node(1)
                if sampleNode.__dict__.keys() == o.keys():
                    continue
            _id = id(o)
            if not self.repeat and (_id in self.already_included):
                if self.str_func is not None: s = self.str_func(o)
                else: s = str(o)
                res.children.append("%s (already included, id %s)" %\
                                    (s, _id))
                continue
            if (not isinstance(o, _Node)) and (o not in self.ignore):
                res.children.append(self._get_tree(o, maxdepth-1))
        return res

class ConsoleBrowser(RefBrowser):
    """RefBrowser implementation which prints the tree to the console.

    If you don't like the looks, you can change it a little bit.
    The class attributes 'hline', 'vline', 'cross', and 'space' can be
    modified to your needs.

    """
    hline = '-'
    vline = '|'
    cross = '+'
    space = ' '

    def print_tree(self, tree=None):
        """ Print referrers tree to console.
        
        keyword arguments
        tree -- if not None, the passed tree will be printed. Otherwise it is
        based on the rootobject.
                   
        """
        if tree == None:
            self._print(self.get_tree(), '', '')
        else:
            self._print(tree, '', '')
        
    def _print(self, tree, prefix, carryon):
        """Compute and print a new line of the tree.

        This is a recursive function.
        
        arguments
        tree -- tree to print
        prefix -- prefix to the current line to print
        carryon -- prefix which is used to carry on the vertical lines
        
        """
        level = prefix.count(self.cross) + prefix.count(self.vline)
        len_children = 0
        if isinstance(tree , _Node):
            len_children = len(tree.children)

        # add vertex
        prefix += str(tree)
        # and as many spaces as the vertex is long
        carryon += self.space * len(str(tree))
        if (level == self.maxdepth) or (not isinstance(tree, _Node)) or\
           (len_children == 0):
            print prefix
            return
        else:
            # add in between connections
            prefix += self.hline
            carryon += self.space
            # if there is more than one branch, add a cross
            if len(tree.children) > 1:
                prefix += self.cross
                carryon += self.vline
            prefix += self.hline
            carryon += self.space

            if len_children > 0:
                # print the first branch (on the same line)
                self._print(tree.children[0], prefix, carryon)
                for b in range(1, len_children):
                    # the caryon becomes the prefix for all following children
                    prefix = carryon[:-2] + self.cross + self.hline
                    # remove the vlines for any children of last branch 
                    if b == (len_children-1):
                        carryon = carryon[:-2] + 2*self.space
                    self._print(tree.children[b], prefix, carryon)
                    # leave a free line before the next branch
                    if b == (len_children-1):
                        if len(carryon.strip(' ')) == 0:
                            return
                        print carryon[:-2].rstrip()

class FileBrowser(ConsoleBrowser):
    """RefBrowser implementation which prints the tree to a file."""
    
    def print_tree(self, filename):
        """ Print referrers tree to file (in text format).
        
        keyword arguments
        tree -- if not None, the passed tree will be printed.
                   
        """
        old_stdout = sys.stdout
        fsock = open(filename, 'w')
        sys.stdout = fsock
        try:
            self._print(self.get_tree(), '', '') 
            sys.stdout = old_stdout
            fsock.close()
        except Exception:
            print "Unexpected error:", sys.exc_info()[0]
        finally:
            sys.stdout = old_stdout
            fsock.close()

# list to hold to referrers
superlist = []
root = "root"
for i in range(3):
    tmp = [root]
    superlist.append(tmp)

def foo(o): return str(type(o))


def print_sample():
    cb = ConsoleBrowser(root, str_func=foo)
    cb.print_tree()

def write_sample():
    fb = FileBrowser(root, str_func=foo)
    fb.print_tree('sample.txt')
    
if __name__ == "__main__":
#    print_sample()
    write_sample()
