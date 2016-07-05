=======
Web app
=======

The web app listens to incoming HTTP connections from breakpad clients, collects
the crash reports, throttles them and stores them as you've configured it.

.. Note::

   If you want to do anything with crashes beyond store them on disk, then you
   don't want to do that in the HTTP request handling cycle--you'll want to use
   :ref:`crashmover app <crashmoverapp>` as a separate process to do the
   heavy-lifting.

App
===

.. autoconfigman:: collector.collector_app.CollectorApp


WSGI app
========

.. autoconfigman:: collector.wsgi_breakpad_collector.BreakpadCollector

.. autoconfigman:: collector.wsgi_generic_collector.GenericCollector
