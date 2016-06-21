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


   In another terminal, you can verify that the containers are running:

   .. code-block:: shell

      $ docker ps


   You can send a crash report into the system and watch it go through the
   steps:

   .. code-block:: shell

      $ ./scripts/send_crash_report.sh


   You should get a CrashID back from the HTTP POST and also be able to follow
   the crash through the docker-compose output.

   .. Note::

      This currently sets up a docker environment that's prod-like and uses
      ``config/prod.env``. We want to support other configurations, but I
      haven't figured out a good way of specifying which environment to use
      which affects containers and configuration and other things. Maybe
      multiple compose files?

5. Run tests:

   .. code-block:: shell

      $ make test

   If you need to run specific tests or pass in different arguments, you can
   do:

   .. code-block:: shell

      $ docker-compose run appbase ./scripts/test.sh [ARGS]

   All ARGS are pass directly to nosetests.


Install (production)
--------------------

FIXME: This may not be right.

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

      # Populate environment with necessary configuration.
      $ gunicorn collector.wsgi --log-file -

7. Run the crashmover:

   .. code-block:: shell

      # Populate environment with necessary configuration.
      $ ./scripts/socorro collector.crashmover_app.CrashMoverApp
