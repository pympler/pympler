import os

from tempfile import NamedTemporaryFile
from shutil import rmtree

from pympler.util.bottle import route, run, template, send_file, redirect

from pympler.gui import charts
from pympler.gui.garbage import GarbageGraph
from pympler.process import ProcessMemoryInfo
from pympler.tracker.stats import Stats


_stats = None
_tmpdir = '.pympler_temp'


@route('/')
def index():
    pmi = ProcessMemoryInfo()
    return template("index", processinfo=pmi)


@route('/process')
def process():
    pmi = ProcessMemoryInfo()
    return template("process", info=pmi)


@route('/tracker')
def tracker_index():
    if _stats:
        for fp in _stats.footprint:
            _stats.annotate_snapshot(fp)
        return template("tracker", snapshots=_stats.footprint)
    else:
        return template("tracker", snapshots=[])


@route('/tracker/distribution')
def tracker_dist():
    fn = os.path.join(_tmpdir, 'distribution.png')
    charts.tracker_timespace(fn, _stats)
    send_file('distribution.png', root=_tmpdir)


@route('/static/:filename')
def static_file(filename):
    send_file(filename, root="views")


@route('/static/img/:filename')
def serve_img(filename):
    send_file(filename, root="views/img")


@route('/garbage')
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
            pass
    return template("garbage", objects=garbage, cycles=cycles)


@route('/garbage/graph/:index')
def garbage_graph(index):
    send_file('%s.png' % index, root=_tmpdir)


@route('/help')
def help():
    redirect('http://packages.python.org/Pympler')


def show(host='localhost', port=8090, tracker=None, stats=None, **kwargs):
    """
    Start the web server to show profiling data. The function does not return
    until the web server is stopped.

    TODO: how to stop the server

    @param host: the host where the server shall run, default is localhost
    @param port: server listens on the specified port, default is 8090 to allow
        coexistance with common web applications
    @param tracker: TODO
    @param stats: TODO
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
    run(host=host, port=port, **kwargs)
    rmtree(_tmpdir)
