======================================
Setting the collector up in production
======================================

Installing dependencies
=======================

Create a virtual environment and install requirements into it:

.. code-block:: shell

   $ mkvirtualenv collector
   $ pip install --require-hashes -r requirements.txt
   $ pip install .


Configuring
===========

The collector is configurable for a variety of situations and needs. You can
configure it with environment variables.

To see a list of all keys:

.. code-block:: shell

   $ ./scripts/socorro collector --admin.print_conf=env > <ENV-FILE>

(Don't forget to activate your virtual environment first.)

You can set these in the environment or put then in a ``.env`` file.

Note that as you change the configuration and add additional components, those
components may also require configuration.

For examples of configuration, see the ``config/`` directory and the rest of
this documentation.

You'll probably want to configure things in this order:

1. Configure the web app and WSGI process.
2. If you're doing anything more than storing crashes on disk, then you're going
   to want to configure the crashmover app, too.
3. Configure any components you're using for throttling, redacting and crash
   storage.

See the relevant parts of this manual.


Running
=======

For production, web app should be run as a WSGI app behind an HTTP proxy
Gunicorn strongly advises Nginx. See the `Gunicorn documentation
<http://gunicorn-docs.readthedocs.org/en/latest/deploy.html>`_ for more details.

If you're also using the crashmover app, that needs to run as a separate process
on the same node as your WSGI app. You could use supervisor or some similar
system to run that, monitor it and keep it running.
