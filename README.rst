=================
Socorro collector
=================

Prototype extracted Socorro breakpad crash collector.

* Free software: Mozilla Public License version 2.0
* Documentation: FIXME


Quickstart
==========

Install
-------

1. Clone the repo:

   .. code-block:: shell

      $ git clone https://github.com/willkg/socorro-collector

   .. Note::

      If you plan on doing development, clone your fork of the repo
      instead.

2. Create a virtualenv:

   .. code-block:: shell

      $ mkvirtualenv collector

3. Install pip 8.0.3 in the collector virtualenv:

   .. code-block:: shell

      $ ./scripts/pipstrap.py

4. Install requirements and socorro-collector in the collector virtualenv.

   For production:

   .. code-block:: shell

      $ pip install --require-hashes -r requirements.txt
      $ pip install .

   For development:

   .. code-block:: shell

      $ pip install --require-hashes -r requirements-dev.txt
      $ pip install -e .


Running in a dev environment
----------------------------

FIXME


Running tests
-------------

Run in the collector virtualenv:

.. code-block:: shell

   $ ./scripts/test.sh

This runs nosetests. It'll pass any arguments you provide to nose.
