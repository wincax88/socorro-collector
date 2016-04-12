==================================
Rewrite collector project (2016q2)
==================================

:author:  Will Kahn-Greene
:history:
          * 2016-03-31: Initial writing
          * 2016-04-08: Draft 1 PR
          * 2016-04-18: Rewrite based on pr comments, discussion with Peter and
            lots more research

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


Requirements
============

1. General requirements
-----------------------

REQ 1.1: Have lots of 9s for uptime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

REQ 1.2: Not drop crashes on the floor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Possible scenarios:

* can't connect to s3 for a long time
* deploying a new collector
* switch s3 buckets which requires a configuration change and a deployment
* collector process crashes, but server is still around
* others?

REQ 1.3: Handle network and external resource problems gracefully
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Clients on slow connections that take a lonnnnnng time to upload a crash.
* S3 availability issues, slowness, network issues, outages, etc.
* RabbitMQ availability issues, network issues, outages, etc.

REQ 1.4: 12-factor compliant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Collector should have the properties of 12-factor compliant applications:
  http://12factor.net/

As a proxy for this, we're going to require that this runs on Heroku. If it runs
on Heroku, then it's probably sufficiently 12-factor to not require complex
infrastructure and unicorns.

Bonus points if we can add a "Deploy to Heroku" button in the README that shows
up on GitHub and have that work.

REQ 1.5: Run in production as a single process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, the collector has a WSGI-based process that dumps crashes to the
file system and generates uuids and then another process that runs outside of
the HTTP-request/response cycle, picks crashes off disk, pushes them to s3
and puts the uuid on the process queue.

We want all that to be done with a single process.

REQ 1.6: Configuration changes are tracked in version control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any behavior changes to the collector should be tracked in the repository
alongside the code.

This lets us roll forward and backward.

This gives us an audit trail of what happened, when and why.

REQ 1.7: AWS autoscaled
~~~~~~~~~~~~~~~~~~~~~~~

We want AWS to be able to autoscale the collector to scale with load.

REQ 1.8: Infrastructure for metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We want to know what the collector(s) is doing so that we can determine
improvements, regressions and when the collector(s) is feeling under the
weather.

The current collector wsgi app just logs to syslog. The crashmover logs to
syslog and also sends statsd pings.

The new collector should support both syslog and statsd throughout the collector
and not just in small parts. Adding additional metrics should be
straight-forward.


2. Feature requirements
-----------------------

REQ 2.1: Work with different throttlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current collector has a throttler (LegacyThrottler).

We want the new collector to have the following:

1. a null throttler that is a no-op and is the default out of the box: it should
   log a single line per crash it looked at
2. a throttler that does what the current LegacyThrottler does

REQ 2.2: Work with different storage classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current collector has several storage classes.

We want the new collector to have the following:

1. a null storage class that is a no-op and is the default out of the box: it
   should log a single line per crash stored
2. a file storage class that stores crashes in a specified directory in some
   sensible tree structure
3. an s3 storage class that stores crashes on s3


.. Note::

   Peter pointed out that we could use a fake-s3 for development. If that works
   out, we could nix a file storage class for now.

REQ 2.3: Work with different queueing systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current collector has several queuing classes.

We want the new collector to have the following:

1. a null queueing class that is a no-op and is the default out of the box: it
   should log a single line per crash queued for processing
2. a RabbitMQ class

.. todo:: Might rename this to "notify classes" and make it its own step in the
          pipeline.


REQ 2.4: Support non-breakpad crash reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The current collector handles Breakpad reports as well as Raven reports.

The new collector needs to handle at least Breakpad reports.

The current collector has a generic crash collector in addition to the breakpad
one. The generic collector removes ``\00`` characters from incoming crash
reports.

REQ 2.5: Prod should send stage some reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, the prod collector in the storage step tosses uuids into the stage
processing queue. In this way, we siphon off crashes from prod to our stage
environment.

We should do this with the new collector, too.

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


3. Developer requirements
-------------------------

These are not must-haves, but they're nice-to-haves that affect new development
and ongoing maintenance.

REQ 3.1: Easy to set up a dev environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It should be easy to go from cloning the git repository to having a running
collector in a dev environment.

A good litmus test here would be "can we explain the quick start in the README?"

REQ 3.2: Easy to configure with sane defaults
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We want sane defaults that make setting it up on Heroku trivial. This should
also make it easy to set up in a dev environment.


Implementation decisions
========================

.. Warning::

   This section is up in the air and this is a stream-of-consciousness pre-draft
   bunch of junk.



Which architecture?
-------------------

coroutine/eventloop
~~~~~~~~~~~~~~~~~~~

Something like gevent gives us asynchronous non-blocking I/O for incoming HTTP
connections as well as outgoing s3 connections. It also gives us an eventloop
for defering work until later and pausing.


peter's plan
~~~~~~~~~~~~

FIXME: needs better header

Have the web framework handle the incoming HTTP request and then try to push it
to S3. If there are problems, store the crash in /tmp/to_store and handle the next
HTTP request.

If all goes well, store in s3. Then check /tmp/to_store and see if there's
anything else that needs storing.

Use a similar method for issues when notifying rabbitmq.

One problem here is that storing to s3 is triggered by incoming HTTP
connections. We'd probably want an endpoint that doesn't take a crash, but
instead triggers storage.


modified peter's plan
~~~~~~~~~~~~~~~~~~~~~

Web framework handles all incoming HTTP requests to ``/submit`` and stores
crashes on disk.

Requests to ``/store-it-now-dammit`` will go through crashes on disk and store
them on s3 if possible.

Have a cron job somewhere that tickles that endpoint periodically.

This is probably easy to implement, but I think it's probably got a lot of edge
case problems.


Other plans
~~~~~~~~~~~

Synchronous IO and use multithreading to run the existing submitter app?


will's current plan
~~~~~~~~~~~~~~~~~~~

Use a WSGI framework library that has minimal requirements and minimal magic.
Doesn't have to be "the best". Good enough is fine. Convenient API is nice.

Use gevent. This gives us non-blocking i/o and concurrent connections, but a
synchronous API. We can constrain the total number of active connections the
process is dealing with at a given time.

Rough algorithm like this:

1. get the crash from the client

   If this fails, log the error, drop the crash and move on (this should only
   fail for bad incoming connections, junk data, etc).

2. save crash to disk

3. throttle the crash (throttler component(s))

   * This shouldn't fail because it shouldn't depend on anything external. If it
     does fail, that's a bug.
   * Try to reuse existing socorro code.

4. store the crash (crashstorage component(s))

   * If this fails, retry in 5 minutes? Logarithmic retry timeout? Use gevent.sleep.
   * Try to reuse existing socorro code.

5. notify about the crash (notifier component(s))

   * If this fails, retry in 5 minutes? Logarithmic retry timeout? Use gevent.sleep.
   * Try to reuse existing socorro code.

6. delete crash from disk


Components
----------

Current collector has notifying rabbitmq as a storage class. We might want to
make notification a separate step:

1. get the crash from the client
2. throttle the crash
3. store the crash
4. notify about the crash

We could write that structure as a component, so then the collector would have:

1. get the crash from the client
2. process the crash

   Mozilla processor would have:

   1. throttle
   2. store
   3. notify

That seems a bit much, though. Probably better not to have that additional
layer for now.

We could also just treat it like a regular pipeline where each component is a
transform and we build a list of them and just go through them one at a time.
This gets tricky when one step does something that requires it to skip other
steps because it doesn't know about other steps.

We could track tags with the crash and components could change their behavior
based on tags. For example, a crash with "CRASH-REJECTED" would just pass
through the pipeline because no one wants to do anything with it.

The problem here is that it's hard to discover components and hard to understand
the system, but it'd be more flexible than one where the steps are hard-coded.


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

I think this is "Yes" until we hit a compelling "No". We'd use configman for:

* configuration
* plugin infrastructure supporting plugins that have their own configuration

If we didn't use it, we'd have to replace those things with other things. Peter
mentioned using python-decouple for configuration. I've written plugin
frameworks before.

We should note that even if we do use the configman library, we're not married
to the way socorro uses configman. Particularly the kinds of components involved
and their roles.

If we use configman, we might be able to copy the relevant socorro components
over and adjust them rather than rewrite them wholesale.

.. todo:: Read through configman more.


Should we use socorro or socorrolib?
------------------------------------

No. The collector should be self-contained and completely unaffected by changes
to socorro and socorrolib repositories. This is particularly important for the
collector because of its uptime requirements.

The sucky part of this is that we'll end up with some code redundancy. But, so
it goes.


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

.. todo:: Flesh this out.


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

.. todo:: Talk to Rob about collector features

.. todo:: peter says there's the feature for two http posts each holding a
          crash, but they're connected--do they get connected with the collector
          or elsewhere?

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


requestb.in
-----------

could we build this such that people could throw together their own requestb.in
type sites? is that helpful? does that cause us to abstract too much?
