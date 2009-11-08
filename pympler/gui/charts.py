"""
Generate charts from gathered data.

Requires **matplotlib**.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def tracker_timespace(filename, stats):
    """
    Create a time-space chart from a ``Stats`` instance.
    """    
    classlist = list(stats.index.keys())
    classlist.sort()

    x = [fp.timestamp for fp in stats.footprint]
    base = [0] * len(stats.footprint)
    poly_labels = []
    polys = []
    for cn in classlist:
        stats.annotate_snapshot(fp)
        pct = [fp.classes[cn]['pct'] for fp in stats.footprint]
        if max(pct) > 3.0:
            sz = [float(fp.classes[cn]['sum'])/(1024*1024) for fp in stats.footprint]
            sz = list(map( lambda x, y: x+y, base, sz ))
            xp, yp = matplotlib.mlab.poly_between(x, base, sz)
            polys.append( ((xp, yp), {'label': cn}) )
            poly_labels.append(cn)
            base = sz

    fig = plt.figure(figsize=(10,4))
    ax = fig.add_subplot(111)

    ax.set_title("Snapshot Memory")
    ax.set_xlabel("Execution Time [s]")
    ax.set_ylabel("Virtual Memory [MiB]")

    y = [float(fp.asizeof_total)/(1024*1024) for fp in stats.footprint]
    p1 = ax.plot(x, y, 'r--', label='Total')
    y = [float(fp.tracked_total)/(1024*1024) for fp in stats.footprint]
    p2 = ax.plot(x, y, 'b--', label='Tracked total')

    for (args, kwds) in polys:
        ax.fill(*args, **kwds)
    ax.legend(loc=2) # TODO fill legend
    fig.savefig(filename)
