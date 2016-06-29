================
Developer errata
================

Code
====

All code files need to start with the MPLv2 header::

    # This Source Code Form is subject to the terms of the Mozilla Public
    # License, v. 2.0. If a copy of the MPL was not distributed with this
    # file, You can obtain one at http://mozilla.org/MPL/2.0/.

To lint your code, do:

.. code-block:: shell

    $ make lint

If you hit issues, use ``# noqa``.


Documentation
=============

Documentation is compiled with `Sphinx <http://www.sphinx-doc.org/>`_ and is
available on ReadTheDocs.

To build the docs, run this:

.. code-block:: shell

    $ make docs


Testing
=======

To run the tests, run this:

.. code-block:: shell

   $ make test

This runs ``./scripts/test.sh`` in the appbase container. You can do this by
hand like this:

.. code-block:: shell

   $ docker-compose run appbase ./scripts/test.sh [TEST-ARGS]

which lets you pass in additional args to the nose test runner.

To run the tests with coverage, do:

.. code-block:: shell

   $ make test-coverage

You can also send test crashes to a running collector on localhost:8000 using:

.. code-block:: shell

   $ ./scripts/send_crash_report.sh
