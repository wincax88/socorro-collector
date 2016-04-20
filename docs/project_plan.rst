==================================
Rewrite collector project (2016q2)
==================================

:author:  Will Kahn-Greene
:history:
          * 2016-03-31: Initial writing
          * 2016-04-08: Draft 1 PR
          * 2016-04-18: Rewrite based on pr comments, discussion with Peter and
            lots more research
          * 2016-04-19: Overhaul after talking with Chris

.. contents::


Timeline
========

This is mostly so we have some rough idea about the project.

April 2016: Research existing collector, establish requirements, figure out what
properties the thing we're building needs to have and what it needs to do.

May 2016: Benchmark architecture ideas. Settle on architecture. Implement. Get
set up in CI. Write docs.

June 2016: Load test, build environments.

July 2016: Push to production. Switch from current collector to new one.


Mission
=======

We're rewriting the collector with the following goals:

1. self-contained in its own repository and doesn't depend on socorro and
   socorrolib repositories

2. can be deployed on its own (as opposed to deployed with the rest of socorro)

3. drop in replacement for the current collector which makes it easier to
   transition to: it accepts HTTP POSTs like the current collector, it stores
   crashes to s3 and it tosses items in the rabbitmq processor queue


Assumptions
===========

Here are some assumptions about this project and the environment that we're
accepting for now:

1. The new collector will operate in a Heroku-like environment.

2. We're going to use Python for the new collector.

3. We have at least the same amount of operating budget for the collector as we
   have now.

4. There are a few other projects at Mozilla that perform similar roles. It's
   likely these will converge in some way.

   Given that, I'm building a collector that'll last 2 years.


Requirements
============

1. General requirements
-----------------------

REQ 1.1: Have lots of 9s for uptime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

REQ 1.2: Avoid dropping crashes on the floor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Possible scenarios:

* can't connect to s3 for a long time
* deploying a new collector
* switch s3 buckets which requires a configuration change and a deployment?

REQ 1.3: Handle network and external resource problems gracefully
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Clients on slow connections that take a lonnnnnng time to upload a crash.
* S3 availability issues, slowness, network issues, outages, etc.
* RabbitMQ availability issues, network issues, outages, etc.

REQ 1.4: 12-factor compliant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Collector should have the properties of 12-factor compliant applications:
  http://12factor.net/

If it runs on Heroku, then it's probably sufficiently 12-factor compliant.

REQ 1.5: Run in production as a single process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, the collector has a WSGI-based process that dumps crashes to the file
system and generates uuids. Then there's the crashmover process that picks
crashes off disk (the disk is being used as a queue), pushes them to s3 and puts
a uuid in the rabbitmq processor queue.

We want all that to be done with a single process making it easier to run.

REQ 1.6: Horizontally autoscaled
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We're using AWS currently and we want the autoscaler to work with the new
collector.

Things we might want to use for triggering scaling:

1. size of queue of crashes to store in s3: this indicates the node is backing
   up

2. disk/memory usage?

REQ 1.7: Infrastructure for metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We want to know what the collector(s) is doing so that we can determine
improvements, regressions and when the collector(s) is feeling under the
weather.

The current collector wsgi app just logs to syslog. The crashmover logs to
syslog and also sends statsd pings.

The new collector should support both syslog and statsd throughout the collector
and not just in small parts. Adding additional metrics should be
straight-forward.

REQ 1.8: Run for weeks on end
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plan is that we're not going to be deploying new collectors often. Given
that, a collector process might run for weeks.

REQ 1.9: Be self contained
~~~~~~~~~~~~~~~~~~~~~~~~~~

The current collector is part of the socorro repository and depends on
socorrolib.

The new collector will be self-contained and not depend on either socorro or
socorrolib.


2. Feature requirements
-----------------------

REQ 2.1: Has a configrable throttler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current collector has a throttler (LegacyThrottler).

I think for now, we're going to do things the same way, but at some point in the
future, we want a throttler that's easier to configure.

REQ 2.2: Stores crashes on s3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We need to store crashes on s3.

This is a critical step in order to not drop crashes on the floor.

For development purposes, it might help to have another storage class that works
with local dev environments better, but maybe fake-s3 is fine for this.

REQ 2.3: Use hierarchical pseudo filenames in s3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Rob said the current collector creates files like::

    {bucket}/v1/processed_crash/0bba929f-8721-460c-dead-a43c20071027


But that's not helpful and it takes a long time to list the bucket. A better way
would be::

    {bucket}/v1/processed_crash/20071027/0bba929f-8721-460c-dead-a43c


Then we can use prefixes.

When we do this, then we should switch from v1 to v2.

REQ 2.4: Queue crashes for processing via rabbitmq
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current collector queues crashes for processing as part of the storage class
lineup.

We don't want to queue a crash for processing until it's been stored on s3.

.. Note::

   The current collector in prod also selects some crashes and queues them in
   the stage processing queue for processing on stage. We should do this or
   something equivalent.

REQ 2.5: Handle breakpad crash reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current collector handles Breakpad reports as well as Raven reports.

The new collector needs to handle at least Breakpad reports.

The current collector has a generic crash collector in addition to the breakpad
one. The generic collector removes ``\00`` characters from incoming crash
reports.

REQ 2.6: Track metrics
~~~~~~~~~~~~~~~~~~~~~~

We want to track something like the following:

* incoming crash ping
* throttle result ping
* crash-accepted ping
* crash-deferred ping
* crash-rejected ping
* crash-stored ping
* others?

FIXME: Other feature requirements here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


3. Other requirements
---------------------

These are nice-to-haves and things to think about:

1. Easy to set up a dev environment. A good litmus test for this would be "can
   we explain the quick start in the README?"

2. The configuration defaults should be sane and make setting it up on Heroku
   and/or a dev environment easy.



Implementation decisions
========================

.. Warning::

   This section is up in the air and this is a stream-of-consciousness pre-draft
   bunch of junk.


Language
--------

We'll use Python. The rest of Socorro is in Python, we have a lot of Python
expertise, etc.


Which web framework?
--------------------

Things we might want (FIXME!):

* Works on Heroku.
* No db.
* Minimal dependencies.
* Good documentation.
* Mature.
* Minimal footprint.
* Minimal magic.
* At least as "good" as CherryPy.

Maybe these, too:

* gevent support
* WSGI compliant

Possibilities:

* gunicorn or uwsgi

  * gunicorn is pure python which might be easier to deal with, test and deploy
  * uwsgi seems more configurable -- anything compelling?
  * we're using uwsgi now

* gunicorn/uwsgi + flask/falcon/bottle + gevent

  uses gevent for non-blocking io and coroutines

* gunicorn/uwsgi + flask/falcon/bottle

  block on io. maybe use Peter's idea of cleaning up?


Should we use configman for configuration?
------------------------------------------

Maybe a "Yes" until we hit a compelling "No".

We currently use configman for:

* configuration
* component infrastructure supporting components that have their own
  configuration
* runtime dependency injection

If we didn't use it, we'd have to replace those things with other things. Peter
mentioned using python-decouple for configuration. I've written plugin
frameworks before.

We should note that even if we do use the configman library, we're not married
to the way socorro uses configman. Particularly the kinds of components involved
and their roles. Further, we don't have to put everything into configuration. We
could have some things in configuration and other things specified in code.

If we do use configman, we don't want to be in the situation we're currently in
where large swaths of behavior are specified in configuration in consul where
there's no audit trail and it's impossible to tell how it works from reading
through the code in the repository.

If we do use configman, we might be able to copy the relevant socorro components
over and tweak them rather than rewrite them wholesale. Further, we might be
able to reuse configuration--the transition from the old collector to the new
one might be easier.

Still to be decided at a later point.


Architecture
------------

I'm currently hedging towards something like this:

Use a WSGI framework library that has minimal requirements and minimal magic.
Doesn't have to be "the best". Good enough is fine. Convenient API is nice.
Bottle? Flask? Falcon?

Use gevent which gives us non-blocking i/o and concurrent connections, but a
synchronous API. We can constrain the total number of active connections the
process is dealing with at a given time.

Rough algorithm could be like this:

1. get the crash from the client

   If this fails, log the error, drop the crash and move on (this should only
   fail for bad incoming connections, junk data, etc).

2. save crash to disk

   This makes sure the crash is *somewhere* that's manually accessible if things
   go to hell.

3. throttle the crash

   * This shouldn't fail because it shouldn't depend on anything external. If it
     does fail, that's a bug.
   * Try to reuse existing socorro code.

4. store the crash on s3

   * If this fails, use gevent.sleep to retry in x minutes.
   * Try to reuse existing socorro code.

5. notify about the crash

   * If this fails, use gevent.sleep to retry in x minutes.
   * Try to reuse existing socorro code.

6. delete crash from disk

This hasn't been benchmarked, load tested, etc.


Oddball notes
=============

Current collector
-----------------

Notes about the current collector:


Overall structure
~~~~~~~~~~~~~~~~~

In production, we run two processes:

1. WSGI process
2. submitter process


WSGI process
~~~~~~~~~~~~

The WSGI process handles incoming HTTP requests, pulls out the crash, throttles
it and then (depending on the throttling outcome) stores it on disk. This is the
CollectorApp.

It pulls configuration from socorro-infra conf files and also consul.

socorro-infra has this in ``collector.conf``::

  storage.crashstorage_class=socorro.external.fs.crashstorage.FSTemporaryStorage
  web_server.wsgi_server_class=socorro.webapi.servers.WSGIServer


.. todo:: Seems like we're using WSGIServer (which uses web.py) and not CherryPy
          in production. Is that true?


Submitter process
~~~~~~~~~~~~~~~~~

The submitter process runs via cron. It looks at the disk and for each crash on
disk, stores it in s3 and rabbitmq.

socorro-infra has this in ``crashmover.conf``::

  destination.crashstorage_class=socorro.external.crashstorage_base.PolyCrashStorage
  destination.storage_classes=socorro.external.rabbitmq.crashstorage.RabbitMQCrashStorage, socorro.external.boto.crashstorage.BotoS3CrashStorage
  destination.storage0.crashstorage_class=socorro.external.rabbitmq.crashstorage.RabbitMQCrashStorage
  destination.storage1.benchmark_tag=S3BenchmarkWrite
  destination.storage1.crashstorage_class=socorro.external.crashstorage_base.BenchmarkingCrashStorage
  destination.storage1.wrapped_crashstore=socorro.external.boto.crashstorage.BotoS3CrashStorage
  producer_consumer.maximum_queue_size=24
  producer_consumer.number_of_threads=12
  source.crashstorage_class=socorro.external.fs.crashstorage.FSTemporaryStorage

The submitter app has a pause between submission queueing. Why? Is the queueing
system flaky?

    Rob says this is from bygone days and we probably don't need this anymore.


Submitter utility
~~~~~~~~~~~~~~~~~

Additionally, there's ``socorro/collector/breakpad_submitter_utilities.py``
which is a utility for pushing crashes at a collector sitting at a specified
url.


Throttler
~~~~~~~~~

The collector is using the LegacyThrottler
(``socorro/collector/throttler.py::LegacyThrottler``). It's named this because
at one point there was going to be a new throttler, but that work never
completed. The throttler throttles based on the ``throttle_conditions`` rules.

.. todo:: What're the rules we're using now? Is it the default value?


Collectors
~~~~~~~~~~

We have two kinds of collectors:

* generic collector (``socorro/collector/wsgi_generic_collector.py::GenericCollector``)
* breakpad collector
  (``socorro/collector/wsgi_breakpad_collector.py::BreakpadCollector2015`` or
  ``BreakpadCollector``)

In generic collector, there's a boolean that suggests we use the crash id
provided in the crash submission. Why would we ever want to do that?

    Rob says this is to let us inject crashes from -prod into -stage with the
    same crash id. That's pretty handy.

The collector generates a checksum for each dump and creates a hash of that. Why?

    It's not used anywhere else in the collector, but we should assume it's used
    later down the line.

    Maybe we can hardcode this to simplify things rather than keeping it as a
    component?


Routes
~~~~~~

Dynamic configuration-based url binding to collectors

* breakpad collector: ``/submit`` url for collecting normal things
* generic collector: ``/some/other/uri`` url for collecting generic things

url binding happens at run-time based on ``services_controller`` configuration.

Production currently just has a collector bound to ``/submit``.


HTTP POSTs
~~~~~~~~~~

Crashes come in to ``/submit`` as an HTTP POST.

A crash is a multi-part HTML form post.

* form POSTs are gzipped
* each crash comes with one or more associated dumps

.. todo:: Flesh this out.

.. todo:: peter says there's the feature for two http posts each holding a
          crash, but they're connected--do they get connected with the collector
          or elsewhere?


Storage classes
~~~~~~~~~~~~~~~

Crashes are initially stored by the WSGI handler onto the file system.

The submitter app pulls the crashes off the file system and sends them to s3 and
then rabbitmq. For rabbitmq, the "storage" is really just adding the uuid to the
processor queue.

``socorro/collector/breakpad_submitter_utilities.py::BreakpadPOSTDestination``

    Pushes crashes to a specified url.

``socorro.external.fs.crashstorage.FSLegacyDatedRadixTreeStorage``

    Stores crashes on the file system.


Metrics and logging
~~~~~~~~~~~~~~~~~~~

Seems like everything is set up to log to syslog. We're not using statsd for the
collector, but we do use it for the crashmover.


Other collector notes
~~~~~~~~~~~~~~~~~~~~~

There are 10 collectors running in production right now.

Outstanding questions:

.. todo:: Are there other collector features we're missing here?

.. todo:: make sure that if s3 has a major outage or api change or we have to
          switch s3 accounts or buckets or something crazy that requires us to
          deploy a new collector that we have some way of retrieving crashes
          that we've captured.

          I think this means we need to get the crash from the client and stick
          it on disk and use disk for ephemeral storage.


load testing
------------

load testing

* http://blog.ziade.org/2012/08/22/marteau-distributed-load-tests/

  funkload and marteau

.. todo:: Talk to Tarek about load testing.


gevent and other architecture thoughts
--------------------------------------

use gevent?

* coroutine based event loop
* single thread
* allows for non-blocking i/o
* event loop for adding other events to be done to
* yielding control is explicit, so this doesn't require locking, semaphores and
  other synchronization techniques that threads do
* ``gevent.spawn(CALLABLE, timeout=SECONDS)`` will create a new event and put it
  in the event queue
* can create the WSGIServer with a pool that specifies how many connections it
  can handle at a given time. see ``gevent.pool.Pool``

.. todo:: need to think about making sure the incoming http requests don't
          oversaturate later steps.

          we don't want http handling super fast and s3 super slow and thus we
          end up with a ton of s3 stuff.

          how does this naturally throttle itself?

.. todo:: Think about /tmp/inbound and /tmp/outbound architecture Peter brought up:
          https://github.com/willkg/socorro-collector/pull/1/files#r59208838


Research links
==============

* cherrypy:

  * http://cherrypy.org/

* flask framework:

  * http://flask.pocoo.org/

* bottle framework:

  * http://bottlepy.org/docs/dev/index.html
  * http://bottlepy.org/docs/dev/async.html

* falcon framework:

  * http://falconframework.org/

* gevent:

  * http://www.gevent.org/
  * https://sdiehl.github.io/gevent-tutorial/

* gunicorn:

  * http://gunicorn.org/

* heroku button:

  * https://blog.heroku.com/archives/2014/8/7/heroku-button

* python fake s3:

  * https://github.com/jserver/mock-s3

* python mock s3 for tests:

  * https://pypi.python.org/pypi/moto/0.4.6

* planes article that talks about issues with mono-repos vs. separated repos
  amongst other things

  * http://www.paperplanes.de/2013/10/18/the-smallest-distributed-system.html
