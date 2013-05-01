"""
Expose a memory-profiling panel to the Django Debug toolbar.

Requires Django and Django Debug toolbar:

https://github.com/django-debug-toolbar/django-debug-toolbar

This memory panel is a third party addon (not included by default)
that can be added by overriding `DEBUG_TOOLBAR_PANELS` setting:

    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        ...
        'pympler.debug_panel.MemoryProfilerPanel',
    )
"""

from pympler.process import ProcessMemoryInfo

try:
    from debug_toolbar.panels import DebugPanel
    from django.template.loader import render_to_string
except ImportError:
    class DebugPanel(object):
        pass


class MemoryProfilerPanel(DebugPanel):

    name = 'pympler'

    has_content = True

    template = 'debug_toolbar/panels/timer.html'

    def process_request(self, request):
        self._before = ProcessMemoryInfo()

    def process_response(self, request, response):
        self._after = ProcessMemoryInfo()

    def title(self):
        return 'Memory'

    def nav_title(self):
        return 'Memory'

    def url(self):
        return ''

    def get_stats(self):
        pass

    def content(self):
        context = self.context.copy()
        rows = self._after - self._before
        context.update({'rows': rows})
        return render_to_string(self.template, context)
