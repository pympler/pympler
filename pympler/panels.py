"""
Expose a memory-profiling panel to the Django Debug toolbar.

Requires Django and Django Debug toolbar:

https://github.com/django-debug-toolbar/django-debug-toolbar

This memory panel is a third party addon (not included by default)
that can be added by overriding the `DEBUG_TOOLBAR_PANELS` setting:

    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        ...
        'pympler.panels.MemoryPanel',
    )
"""

from pympler.classtracker import ClassTracker
from pympler.process import ProcessMemoryInfo
from pympler.util.stringutils import pp

try:
    from debug_toolbar.panels import DebugPanel
    from django.db.models import get_models
    from django.template.loader import render_to_string
except ImportError:
    class DebugPanel(object):
        pass


class MemoryPanel(DebugPanel):

    name = 'pympler'

    has_content = True

    template = 'debug_toolbar/panels/timer.html'

    def process_request(self, request):
        self._tracker = ClassTracker()
        for model in get_models():
            self._tracker.track_class(model, keep=True)
        self._tracker.create_snapshot('before')
        self._before = ProcessMemoryInfo()

    def process_response(self, request, response):
        self._after = ProcessMemoryInfo()
        self._tracker.create_snapshot('after')

    def title(self):
        return 'Memory'

    def nav_title(self):
        return 'Memory'

    def nav_subtitle(self):
        vsz = self._after.vsz
        delta = vsz - self._before.vsz
        return "VSZ: %s (+%s)" % (pp(vsz), pp(delta))

    def url(self):
        return ''

    def get_stats(self):
        pass

    def content(self):
        stats = self._tracker.stats
        stats.annotate()
        self._tracker.clear()
        context = self.context.copy()
        rows = [('Resident set size', self._after.rss),
                ('Virtual size', self._after.vsz),
                ]
        rows.extend(self._after - self._before)
        rows = [(key, pp(value)) for key, value in rows]
        rows.extend(self._after.os_specific)
        snapshot = stats.snapshots[-1]
        for model in stats.tracked_classes:
            cnt = snapshot.classes.get(model, {}).get('active', 0)
            size = snapshot.classes.get(model, {}).get('sum', 0)
            rows.append((model, "%s (%d)" % (pp(size), cnt)))
        context.update({'rows': rows})
        return render_to_string(self.template, context)
