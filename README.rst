=================
Socorro collector
=================

Prototype extracted Socorro breakpad crash collector.

* Free software: Mozilla Public License version 2.0
* Documentation: FIXME


Quickstart
==========

Install (dev)
-------------

1. Clone the repository:

   .. code-block:: shell

      $ git clone https://github.com/<YOUR-FORK>/socorro-collector

2. Install docker and docker-compose

3. Build:

   .. code-block:: shell

      $ make build

4. Run:

   .. code-block:: shell

      $ make run

5. Run tests:

   .. code-block:: shell

      $ make test


Install (production)
--------------------

1. Clone the repo:

   .. code-block:: shell

      $ git clone https://github.com/willkg/socorro-collector

2. Create a virtualenv with Python 2.7:

   .. code-block:: shell

      $ mkvirtualenv collector

3. Install pip 8.0.3 in the collector virtualenv:

   .. code-block:: shell

      $ ./scripts/pipstrap.py

4. Install requirements and socorro-collector in the collector virtualenv:

   .. code-block:: shell

      $ pip install --require-hashes -r requirements.txt
      $ pip install .

5. Configure the collector.

6. Run the web app:

   .. code-block:: shell

      $ ./scripts/dotenv <ENV-FILE> gunicorn collector.wsgi --log-file -

7. Run the crashmover:

   .. code-block:: shell

      $ ./scripts/dotenv <ENV-FILE> ./scripts/socorro collector.crashmover_app.CrashMoverApp


Running tests
-------------

Run in the collector virtualenv:

.. code-block:: shell

   $ ./scripts/test.sh

This runs nosetests. It'll pass any arguments you provide to nose.
