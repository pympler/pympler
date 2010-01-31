"""
Web-based profiling interface. Exposes process information, tracker statistics,
and garbage graphs.
"""

import os

from tempfile import NamedTemporaryFile
from shutil import rmtree

from pympler.util.compat import bottle

from pympler import DATA_PATH
from pympler.gui import charts
from pympler.gui.garbage import GarbageGraph
from pympler.process import ProcessMemoryInfo
from pympler.tracker.stats import Stats


class Cache(object):
    """
    Cache internal structures (garbage graphs, tracker statistics).
    """
    def __init__(self):
        self.stats = None
        self.garbage_graphs = None

    def clear(self):
        self.garbage_graphs = None


cache = None


_tmpdir = '.pympler_temp'

static_files = os.path.join(DATA_PATH, 'templates')

bottle.TEMPLATE_PATH.append(static_files)


@bottle.route('/')
def index():
    pmi = ProcessMemoryInfo()
    return bottle.template("index", processinfo=pmi)


@bottle.route('/process')
def process():
    pmi = ProcessMemoryInfo()
    return bottle.template("process", info=pmi)


@bottle.route('/tracker')
def tracker_index():
    global cache

    stats = cache.stats
    if stats:
        for fp in stats.footprint:
            stats.annotate_snapshot(fp)
        return bottle.template("tracker", snapshots=stats.footprint)
    else:
        return bottle.template("tracker", snapshots=[])


@bottle.route('/refresh')
def refresh():
    global cache
    cache.clear()
    bottle.redirect('/')


@bottle.route('/tracker/distribution')
def tracker_dist():
    fn = os.path.join(_tmpdir, 'distribution.png')
    charts.tracker_timespace(fn, _stats)
    bottle.send_file('distribution.png', root=_tmpdir)


@bottle.route('/static/:filename')
def static_file(filename):
    bottle.send_file(filename, root=static_files)


@bottle.route('/static/img/:filename')
def serve_img(filename):
    bottle.send_file(filename, root="templates/img")


def _compute_garbage_graphs():
    """
    Retrieve garbage graph objects from cache, compute if cache is cold.
    """
    global cache
    if cache.garbage_graphs is None:
        cache.garbage_graphs = GarbageGraph().split_and_sort()
    return cache.garbage_graphs


@bottle.route('/garbage')
def garbage_index():
    garbage_graphs = _compute_garbage_graphs()
    return bottle.template("garbage_index", graphs=garbage_graphs)


@bottle.route('/garbage/:index')
def garbage(index):
    graph = _compute_garbage_graphs()[int(index)]
    garbage = graph.metadata
    garbage.sort(key=lambda x: -x.size)
    return bottle.template("garbage", objects=garbage, index=index)


@bottle.route('/garbage/graph/:index')
def garbage_graph(index):
    graph = _compute_garbage_graphs()[int(index)]
    graph._reduce_to_cycles() # TODO : changes cached graph
    try:
        graph.render(os.path.join(_tmpdir, '%d.png' % graph.index), format='png')
    except OSError:
        pass
    bottle.send_file('%s.png' % index, root=_tmpdir)


@bottle.route('/help')
def help():
    bottle.redirect('http://packages.python.org/Pympler')


def show(host='localhost', port=8090, tracker=None, stats=None, **kwargs):
    """
    Start the web server to show profiling data. The function suspends the
    Python application (the current thread) until the web server is stopped.

    TODO: how to stop the server

    During the execution of the web server, profiling data is (lazily) cached
    to improve performance. For example, garbage graphs are rendered when the
    garbage profiling data is requested and are simply retransmitted upon later
    requests.

    :param host: the host where the server shall run, default is localhost
    :param port: server listens on the specified port, default is 8090 to allow
        coexistance with common web applications
    :param tracker: TODO
    :param stats: TODO
    """
    global cache
    cache = Cache()

    if tracker and not stats:
        cache.stats = Stats(tracker=tracker)
    else:
        cache.stats = stats
    try:
        os.mkdir(_tmpdir)
    except OSError:
        pass
    bottle.run(host=host, port=port, **kwargs)
    rmtree(_tmpdir)
