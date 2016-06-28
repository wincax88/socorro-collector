=================
Socorro collector
=================

Collector is a WSGI application. Its task is to accept incoming crash reports
from remote clients and save them in a place and format usable by further
applications.

Raw crashes are accepted via HTTP POST. The form data from the POST is then
arranged into a JSON and saved into the local file system. The collector is
responsible for assigning an ooid? (Our Own ID) to the crash. It also assigns a
Throttle? value which determines if the crash is eventually to go into the
relational database.

Should the saving to a local file system fail, there is a fallback storage
mechanism. A second file system can be configured to take the failed saves. This
file system would likely be an NFS mounted file system.

* Free software: Mozilla Public License version 2.0
* Documentation: https://socorro-collector.readthedocs.io/


Quickstart
==========

This is a quickstart using Docker to see how the pieces work and also for local
development.

For more comprehensive documentation or instructions on how to set this up in
production, see `the manual on ReadTheDocs
<https://socorro-collector.readthedocs.io/>`_.

1. Clone the repository:

   .. code-block:: shell

      $ git clone https://github.com/<YOUR-FORK>/socorro-collector

2. Install docker and docker-compose

3. Build:

   .. code-block:: shell

      $ make build

4. Run with a simple development configuration:

   .. code-block:: shell

      $ make run


   You should see a lot of output starting like this::

      web_1  | [2016-06-22 15:16:25 +0000] [6] [INFO] Starting gunicorn 19.4.5
      web_1  | [2016-06-22 15:16:25 +0000] [6] [INFO] Listening at: http://0.0.0.0:8000 (6)
      web_1  | [2016-06-22 15:16:25 +0000] [6] [INFO] Using worker: sync
      web_1  | [2016-06-22 15:16:25 +0000] [11] [INFO] Booting worker with pid: 11
      web_1  | 2016-06-22 15:16:25,289 INFO - collector -  - MainThread - app_name: collector
      web_1  | 2016-06-22 15:16:25,290 INFO - collector -  - MainThread - app_version: 4.0
      web_1  | 2016-06-22 15:16:25,290 INFO - collector -  - MainThread - current configuration:

   In another terminal, you can verify that the web container is running:

   .. code-block:: shell

      $ docker ps
      CONTAINER ID    IMAGE                  COMMAND                  CREATED  STATUS  PORTS                   NAMES
      653f09e6136d    socorrocollector_web   "./scripts/run_web.sh"   ...      ...     0.0.0.0:8000->8000/tcp  socorrocollector_web_1

   You can send a crash report into the system and watch it go through the
   steps:

   .. code-block:: shell

      $ ./scripts/send_crash_report.sh
      ...
      <curl http output>
      ...
      CrashID=bp-6c43aa7c-7d34-41cf-85aa-55b0d2160622
      *  Closing connection 0

   You should get a CrashID back from the HTTP POST. You'll also see docker
   logging output something like this::

      web_1  | 2016-06-22 15:19:49,040 INFO - collector -  - MainThread - 8f63752c-57c6-4e5d-b2cf-cabde2160622 received
      web_1  | 2016-06-22 15:19:49,040 DEBUG - collector -  - MainThread - not throttled Test 1.0
      web_1  | 2016-06-22 15:19:49,042 INFO - collector -  - MainThread - 8f63752c-57c6-4e5d-b2cf-cabde2160622 accepted

   When you're done with the process, hit CTRL-C to gracefully kill the docker container.

5. Run tests:

   .. code-block:: shell

      $ make test

   If you need to run specific tests or pass in different arguments, you can
   do:

   .. code-block:: shell

      $ docker-compose run appbase ./scripts/test.sh [ARGS]

   All ARGS are pass directly to nosetests.


.. Note::

   The build and run steps use a very simple dev configuration. You can also use
   the "production configuration" which sets things up similar to the production
   Mozilla Crash Stats system by using the ``build-prod`` and ``run-prod`` make
   rules.


Install (production)
--------------------

FIXME: This may not be right.

1. Clone the repo:

   .. code-block:: shell

      $ git clone https://github.com/mozilla/socorro-collector

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
