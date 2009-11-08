from tools.bottle import route, run, template, send_file

from pympler.process import ProcessMemoryInfo
from pympler.gui.garbage import GarbageGraph
from pympler.tracker.stats import Stats
from pympler.gui import charts

from tempfile import NamedTemporaryFile
from shutil import rmtree

import os


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
    for fp in _stats.footprint:
        _stats.annotate_snapshot(fp)
    return template("tracker", snapshots=_stats.footprint)


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
        cycle.render(os.path.join(_tmpdir, '%d.png' % cycle.index), format='png')
        cycles += 1
    return template("garbage", objects=garbage, cycles=cycles)


@route('/garbage/graph/:index')
def garbage_graph(index):
    send_file('%s.png' % index, root=_tmpdir)


def show(host='localhost', port=8020, tracker=None, stats=None):
    global _stats
    if tracker and not stats:
        _stats = Stats(tracker=tracker)
    else:
        _stats = stats
    os.mkdir(_tmpdir)
    run(host=host, port=port)
    rmtree(_tmpdir) 
