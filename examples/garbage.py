
from pympler.garbagegraph import start_debug_garbage
from pympler import web


class Leaf(object):
    pass


class Branch(object):
    def __init__(self, root):
        self.root = root
        self.leaf = Leaf()


class Root(object):
    def __init__(self, num_branches):
        self.branches = [Branch(self) for _ in range(num_branches)]


start_debug_garbage()

tree = Root(2)
del tree
web.start_profiler(debug=True)
