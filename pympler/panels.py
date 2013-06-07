"""
Expose a memory-profiling panel to the Django Debug toolbar.

Shows process memory information (virtual size, resident set size) and model
instances for the current request.

Requires Django and Django Debug toolbar:

https://github.com/django-debug-toolbar/django-debug-toolbar

Pympler adds a memory panel as a third party addon (not included in the
django-debug-toolbar). It can be added by overriding the `DEBUG_TOOLBAR_PANELS`
setting in the Django project settings::

    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'pympler.panels.MemoryPanel',
        )

Pympler also needs to be added to the `INSTALLED_APPS` in the Django settings::

    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar', 'pympler')
"""

from pympler.classtracker import ClassTracker
from pympler.process import ProcessMemoryInfo
from pympler.util.stringutils import pp

try:
    from debug_toolbar.panels import DebugPanel
    from django.db.models import get_models
    from django.template import Context, Template
    from django.template.loader import render_to_string
except ImportError:
    class DebugPanel(object):
        pass

    class Template(object):
        pass

    class Context(object):
        pass


class MemoryPanel(DebugPanel):

    name = 'pympler'

    has_content = True

    template = 'memory_panel.html'

    classes = [Context, Template]

    def process_request(self, request):
        self._tracker = ClassTracker()
        for cls in get_models() + self.classes:
            self._tracker.track_class(cls, keep=True)
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
        rss = self._after.rss
        delta = rss - self._before.rss
        delta = ('(+%s)' % pp(delta)) if delta > 0 else ''
        return "RSS: %s %s" % (pp(rss), delta)

    def url(self):
        return ''

    def get_stats(self):
        pass

    def content(self):
        stats = self._tracker.stats
        stats.annotate()
        context = self.context.copy()
        rows = [('Resident set size', self._after.rss),
                ('Virtual size', self._after.vsz),
                ]
        rows.extend(self._after - self._before)
        rows = [(key, pp(value)) for key, value in rows]
        rows.extend(self._after.os_specific)

        classes = []
        snapshot = stats.snapshots[-1]
        for model in stats.tracked_classes:
            cnt = snapshot.classes.get(model, {}).get('active', 0)
            size = snapshot.classes.get(model, {}).get('sum', 0)
            if cnt > 0:
                classes.append((model, cnt, pp(size)))
        context.update({'rows': rows, 'classes': classes})
        return render_to_string(self.template, context)
