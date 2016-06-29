.. _crashmoverapp:

==============
Crashmover app
==============

If your collector needs to save crashes to S3 or toss items on a RabbitMQ queue,
then you don't want that work being done during the HTTP request handling cycle.

The crashmover app is a separate process that runs on the same node as the web
app. The web app can be configured to store crashes in a temporary directory on
the node, then the crashmover monitors that directory and handles any storing
work that needs to be done.

.. autoconfigman:: collector.crashmover_app.CrashMoverApp
