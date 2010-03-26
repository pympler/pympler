"""
This module provides a web-based memory profiling interface. The Pympler web
frontend exposes process information, tracker statistics, and garbage graphs.
The web frontend uses `Bottle <http://bottle.paws.de>`_, a lightweight Python
web framework. Bottle is packaged with Pympler.

The web server can be invoked almost as easily as setting a breakpoint using
*pdb*::

    from pympler.gui.web import show
    show()

Calling ``show`` suspends the current thread and executes the Pympler web
server, exposing profiling data and various facilities of the Pympler library
via a graphic interface.

.. note::

    This module requires Python 2.5 or newer.
"""

import sys

if sys.hexversion < 0x02050000:
    raise ImportError("Web frontend requires Python 2.5 or newer.")

import os

from shutil import rmtree
from tempfile import mkdtemp
from wsgiref.simple_server import make_server

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
server = None
tmpdir = None


static_files = os.path.join(DATA_PATH, 'templates')

bottle.TEMPLATE_PATH.append(static_files)


@bottle.route('/')
@bottle.view('index')
def index():
    """Get overview."""
    pmi = ProcessMemoryInfo()
    return dict(processinfo=pmi)


@bottle.route('/process')
@bottle.view('process')
def process():
    """Get process overview."""
    pmi = ProcessMemoryInfo()
    return dict(info=pmi)


@bottle.route('/tracker')
@bottle.view('tracker')
def tracker_index():
    """Get tracker overview."""
    global cache

    stats = cache.stats
    if stats:
        for fp in stats.footprint:
            stats.annotate_snapshot(fp)
        return dict(snapshots=stats.footprint)
    else:
        return dict(snapshots=[])


@bottle.route('/refresh')
def refresh():
    """Clear all cached information."""
    global cache
    cache.clear()
    bottle.redirect('/')


@bottle.route('/tracker/distribution')
def tracker_dist():
    """Render timespace chart for tracker data."""
    fn = os.path.join(tmpdir, 'distribution.png')
    charts.tracker_timespace(fn, _stats)
    bottle.send_file('distribution.png', root=tmpdir)


@bottle.route('/static/:filename')
def static_file(filename):
    """Get static files (CSS-files)."""
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
@bottle.view('garbage_index')
def garbage_index():
    """Get garbage overview."""
    garbage_graphs = _compute_garbage_graphs()
    return dict(graphs=garbage_graphs)


@bottle.route('/garbage/:index')
@bottle.view('garbage')
def garbage(index):
    """Get reference cycle details."""
    graph = _compute_garbage_graphs()[int(index)]
    graph.reduce_to_cycles()
    garbage = graph.metadata
    garbage.sort(key=lambda x: -x.size)
    return dict(objects=garbage, index=index)


def _get_graph(graph, fn):
    """Retrieve or render a graph."""
    try:
        rendered = graph.rendered_file
    except AttributeError:
        try:
            graph.render(os.path.join(tmpdir, fn), format='png')
            rendered = fn
        except OSError:
            rendered = None
    graph.rendered_file = rendered
    return rendered


@bottle.route('/garbage/graph/:index')
def garbage_graph(index):
    """Get graph representation of reference cycle."""
    graph = _compute_garbage_graphs()[int(index)]
    reduce = bottle.request.GET.get('reduce', '')
    if reduce:
        graph = graph.reduce_to_cycles()
    fn = 'garbage%so%s.png' % (index, reduce)
    rendered_file = _get_graph(graph, fn)
    if rendered_file:
        bottle.send_file(rendered_file, root=tmpdir)
    else:
        return None


@bottle.route('/exit')
def kill_server():
    """Kill the server and give the application a chance to continue."""
    # TODO: Find a way to stop server. Raising an exception does not kill the
    # server - only the request. Calling shutdown results in a deadlock.
    global server
    return "Not yet implemented."
    #try:
    #    server.server.shutdown()
    #except AttributeError:
    #    return "ERROR: Stopping the server requires Python 2.6 or newer."


@bottle.route('/help')
def show_documentation():
    """Redirect to online documentation."""
    bottle.redirect('http://packages.python.org/Pympler')


class PymplerServer(bottle.ServerAdapter):
    """Simple WSGI server."""
    def run(self, handler):
        self.server = make_server(self.host, self.port, handler)
        self.server.serve_forever()


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
    global server
    global tmpdir

    cache = Cache()
    tmpdir = mkdtemp(prefix='pympler')

    if tracker and not stats:
        cache.stats = Stats(tracker=tracker)
    else:
        cache.stats = stats
    try:
        os.mkdir(tmpdir)
    except OSError:
        pass
    server = PymplerServer(host=host, port=port, **kwargs)
    try:
        bottle.run(server=server)
    except Exception:
        rmtree(tmpdir)
