"""Graphical user interface for referrers browsing.

The GUI is based on a TreeWidget implemented in IDLE. It is available if you
have Tcl/Tk installed. 


"""
import sys

try:
    import Tkinter
except ImportError:
    print>>sys.__stderr__, "** %s cannot import Tkinter. Your Python may not be"\
                           "configured for Tk. **" % __name__
    sys.exit(1)

from idlelib import TreeWidget

import muppy
import refbrowser
import summary

def default_str_function(o):
    """Default str function for InteractiveBrowser."""
    return summary._repr(o) + '(id=%s)' % id(o)

class _TreeNode(TreeWidget.TreeNode):
    """TreeNode used by the InteractiveBrowser.

    Not to be confused with refbrowser._Node. This one is used in the GUI
    context. 

    """
    def reload_referrers(self):
        """Reload all referrers for this _TreeNode."""
        self.item.node = self.item.reftree._get_tree(self.item.node.o, 1)
        self.item._clear_children()
        self.expand()
        self.update()

    def print_object(self):
        """Print object which this _TreeNode represents to console."""
        print self.item.node.o

    def drawtext(self):
        """Override drawtext from TreeWidget.TreeNode.

        This seems to be a good place to add the popup menu.

        """
        TreeWidget.TreeNode.drawtext(self)
        # create a menu
        menu = Tkinter.Menu(self.canvas, tearoff=0)
        menu.add_command(label="reload referrers", command=self.reload_referrers)
        menu.add_command(label="print", command=self.print_object)
        menu.add_separator()
        menu.add_command(label="expand", command=self.expand)
        menu.add_separator()
        # the popup only disappears when to click on it
        menu.add_command(label="Close Popup Menu")
        def do_popup(event):
            menu.post(event.x_root, event.y_root)
        self.label.bind("<Button-3>", do_popup)
        # override, i.e. disable the editing of items

    # disable editing of TreeNodes
    def edit(self, event=None): pass
    def edit_finish(self, event=None): pass
    def edit_cancel(self, event=None): pass

class _ReferrerTreeItem(TreeWidget.TreeItem, Tkinter.Label):
    """Tree item wrapper around refbrowser._Node object."""

    def __init__(self, parentwindow, node, reftree):
        """You need to provide the parent window, the node this TreeItem
        represents, as well as the tree (refbrowser._Node) which the node
        belongs to.

        """
        Tkinter.Label.__init__(self, parentwindow)
        self.node = node
        self.parentwindow = parentwindow
        self.reftree = reftree

    def _clear_children(self):
        """Clear children list from any TreeNode instances.

        Normally these objects are not required for memory profiling, as they
        are part of the profiler.
        
        """
        new_children = []
        for child in self.node.children:
            if not isinstance(child, _TreeNode):
                new_children.append(child)
        self.node.children = new_children

    def GetText(self):
        return str(self.node)

    def GetIconName(self):
        """Different icon when object cannot be expanded, i.e. has no
        referrers.

        """
        if not self.IsExpandable():
            return "python"

    def IsExpandable(self):
        """An object is expandable when it is a node which has children and
        is a container object. 

        """
        if not isinstance(self.node, refbrowser._Node):
            return False
        else:
            if len(self.node.children) > 0:
                return True
            else:
                return muppy._is_containerobject(self.node.o)

    def GetSubList(self):
        """This method is the point where further referrers are computed.

        Thus, the computation is done on-demand and only when needed.
        
        """
        sublist = []

        children = self.node.children
        if (len(children) == 0) and\
           (muppy._is_containerobject(self.node.o)):
            self.node = self.reftree._get_tree(self.node.o, 1)
            self._clear_children()
            children = self.node.children

        for child in children:
            item = _ReferrerTreeItem(self.parentwindow, child, self.reftree)
            sublist.append(item)
        return sublist

class InteractiveBrowser(refbrowser.RefBrowser):
    """Interactive referrers browser.

    If you do not define str_func, default_str_function will be used.
    
    """
    def main(self, standalone=False):
        """Create interactive browser window.

        keyword arguments
        standalone -- Set to true, if the browser is not attached to other
        windows
        
        """
        if self.str_func == None:
            self.str_func = default_str_function
        window = Tkinter.Tk()
        sc = TreeWidget.ScrolledCanvas(window, bg="white",\
                                       highlightthickness=0, takefocus=1)
        sc.frame.pack(expand=1, fill="both")
        item = _ReferrerTreeItem(window, self.get_tree(), self)
        node = _TreeNode(sc.canvas, None, item)
        node.expand()
        if standalone:
            window.mainloop()

def sample_interactive():
    l = [1,2,3,4,5]
    browser = InteractiveBrowser(l)
    browser.main(standalone=True)

if __name__ == "__main__":
    sample_interactive()
