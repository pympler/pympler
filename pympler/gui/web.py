"""
Web-based profiling interface. Exposes process information, tracker statistics,
and garbage graphs.
"""

import os

from cgi import escape
from tempfile import NamedTemporaryFile
from shutil import rmtree

from pympler.util.compat import bottle

from pympler import DATA_PATH
from pympler.gui import charts
from pympler.gui.garbage import GarbageGraph
from pympler.process import ProcessMemoryInfo
from pympler.tracker.stats import Stats


_stats = None
_tmpdir = '.pympler_temp'

bottle.TEMPLATE_PATH.append(os.path.join(DATA_PATH, 'templates'))


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
    if _stats:
        for fp in _stats.footprint:
            _stats.annotate_snapshot(fp)
        return bottle.template("tracker", snapshots=_stats.footprint)
    else:
        return bottle.template("tracker", snapshots=[])


@bottle.route('/tracker/distribution')
def tracker_dist():
    fn = os.path.join(_tmpdir, 'distribution.png')
    charts.tracker_timespace(fn, _stats)
    bottle.send_file('distribution.png', root=_tmpdir)


@bottle.route('/static/:filename')
def static_file(filename):
    bottle.send_file(filename, root="templates")


@bottle.route('/static/img/:filename')
def serve_img(filename):
    bottle.send_file(filename, root="templates/img")


@bottle.route('/garbage')
def garbage():
    # Get all collectable objects
    gb = GarbageGraph()
    garbage = gb.metadata
    garbage.sort(key=lambda x: -x.size)
    # Get only objects in reference cycles
    gb = GarbageGraph(reduce=True)
    cycles = 0
    for cycle in gb.split():
        try:
            cycle.render(os.path.join(_tmpdir, '%d.png' % cycle.index), format='png')
            cycles += 1
        except OSError:
            break
    # Escape for display in HTML
    for obj in garbage:
        obj.str = escape(obj.str)
    return bottle.template("garbage", objects=garbage, cycles=cycles)


@bottle.route('/garbage/graph/:index')
def garbage_graph(index):
    bottle.send_file('%s.png' % index, root=_tmpdir)


@bottle.route('/help')
def help():
    bottle.redirect('http://packages.python.org/Pympler')


def show(host='localhost', port=8090, tracker=None, stats=None, **kwargs):
    """
    Start the web server to show profiling data. The function suspends the
    Python application (the current thread) until the web server is stopped.

    TODO: how to stop the server

    :param host: the host where the server shall run, default is localhost
    :param port: server listens on the specified port, default is 8090 to allow
        coexistance with common web applications
    :param tracker: TODO
    :param stats: TODO
    """
    global _stats
    if tracker and not stats:
        _stats = Stats(tracker=tracker)
    else:
        _stats = stats
    try:
        os.mkdir(_tmpdir)
    except OSError:
        pass
    bottle.run(host=host, port=port, **kwargs)
    rmtree(_tmpdir)
