.. _django:

=========================
Tracking memory in Django
=========================

Introduction
------------

Pympler includes a memory profile panel for Django that integrates with the
`Django Debug Toolbar <https://github.com/jazzband/django-debug-toolbar>`_. It
shows process memory information and model instances for the current request.

Usage
-----

Pympler adds a memory panel as a third party addon -- it's not included in the
Django Debug Toolbar. It can be added by overriding the `DEBUG_TOOLBAR_PANELS`
setting in the Django project settings::

    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'pympler.panels.MemoryPanel',
        )

Pympler also needs to be added to the `INSTALLED_APPS` in the Django settings::

    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar', 'pympler')

Known issues
------------

Pympler doesn't correctly handle tracking calls from concurrent threads. In
order to get accurate instance counts and sizes, it's recommended to only use
single-threaded web servers for memory profiling, e.g.::

    django-admin runserver --nothreading

.. automodule:: pympler.panels
