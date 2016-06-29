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

Collector supports a number of configuration formats.

Environment variables are recommended.

To see a list of all keys:

.. code-block:: shell

   $ ./scripts/socorro collector --admin.print_conf=env > <ENV-FILE>

(Don't forget to activate your virtual environment first.)

You can set these in the environment or put then in a ``.env`` file.

For examples of configuration, see the ``config/`` directory and the rest of
this documentation.


Running
=======

For production, Collector should be run as a WSGI app behind an HTTP proxy
Gunicorn strongly advises Nginx. See the `Gunicorn documentation
<http://gunicorn-docs.readthedocs.org/en/latest/deploy.html>`_ for more details.
