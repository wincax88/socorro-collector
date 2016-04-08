==================================
Rewrite collector project (2016q2)
==================================

:author:  Will Kahn-Greene
:date:    March 31st, 2016
:history:
          * 2016-03-31: Initial writing
          * 2016-04-08: Draft 1 PR

.. contents::


Notes about the current collector
=================================

.. todo:: Move this to the end of the document after we've got the requirements
          and some of the other bits ironed out.

Notes about the current collector:

* two processes

  1. WSGI process that grabs incoming crashes and stores them on disk (cherrypy
     app)
  2. process that takes them off disk and stores them in the crash storage
     (submiter app)

* ``socorro/collector/breakpad_submitter_utilities.py``: Utility for pushing
  crashes at a collector sitting at a url
* throttlers

* different kinds of collectors

  * breakpad collector (``wsgi_breakpad_collector.BreakpadCollector2015`` or ``BreakpadCollector``)
  * generic collector (``wsgi_generic_collector.GenericCollector``)

* dynamic configuration-based url binding to collectors

  * breakpad collector: ``/submit`` url for collecting normal things
  * generic collector: ``/some/other/uri`` url for collecting generic things

  url binding happens at run-time based on ``services_controller`` configuration

* form POSTs are gzipped

* different kinds of storage classes

* logging infrastructure

* ability to reprocess crashes

.. todo:: Other interesting things about the current collector?


Outstanding questions:

.. todo:: The submitter app has a pause between submission queueing. Why? Is the
          queueing system flaky?

.. todo:: In generic collector, there's a boolean that suggests we use the crash
          id provided in the crash submission. Why would we ever want to do
          that?

.. todo:: Checksum method in generic collector is configurable. Has that ever
          been helpful?

.. todo:: In the configuration, there's a redactor. What's that about?
   

Requirements
============

REQ 1: Reliable and redundant
-----------------------------

Collector should never drop a crash on the floor. Also, lots of 9s.


REQ 2: 12-factor
----------------

As a proxy for this, we're going to require that this runs on Heroku. If it runs
on Heroku, then it's probably sufficiently 12-factor to not require complex
infrastructure and unicorns.

Bonus points if we can add a "Deploy to Heroku" button in the README that shows
up on GitHub and have that work.


REQ 3: Single process
---------------------

Currently, the collector has a WSGI-based process that dumps crashes to the
file system and generates uuids and then another process that runs outside of
the HTTP-request/response cycle, picks crashes off disk, pushes them to s3
and puts the uuid on the process queue.

We want all that to be done with a single WSGI-based process.


REQ 4: Easy to set up
---------------------

Steps to set up a basic collector should be easy to document and easy to follow.


REQ 5: Easy to configure via environment variables and use sane defaults
------------------------------------------------------------------------

We want sane defaults that make setting it up on heroku trivial. That'll also
make it easy to set up in a dev environment.

We want to handle configuration for behavior (use this throttler, use this
storage class, etc) different than configuration for secrets (passwords, etc)
and infrastructure (hosts to connect to, etc). It'd be nice to have
configuration for behavior managed in the repo making it easier to roll
backwards and forwards for behavior changes. Configuration for secrets and
infrastructure should be managed along with the infrastructure.


REQ 6: Scale horizontally
-------------------------

The collector will be behind an ELB. As we're getting crashes, if the collectors
can't keep up, we want AWS to autoscale and increase the number of collectors
involved.

This is probably a natural consequence of being a single process and being
12-factor compliant.


REQ 7: Infrastructure for metrics
---------------------------------

We need infrastructure for gathering metrics from the collector.

The current collector logs to a log file and by grepping/analyzing the log
files, we can determine what's going on.

.. todo:: What should the new collector do?


REQ 8: Work with different throttlers
-------------------------------------

The current collector has a legacy throttler.

We want the new collector to have the following:

1. a null throttler that is a no-op and is the default out of the box: it should
   log a single line per crash it looked at
2. a throttler that does what the current Legacy Throttler does


REQ 9: Work with different storage classes
------------------------------------------

The current collector has several storage classes.

We want the new collector to have the following:

1. a null storage class that is a no-op and is the default out of the box: it
   should log a single line per crash stored
2. a file storage class that stores crashes in a specified directory in some
   sensible tree structure
3. an s3 storage class that stores crashes on s3


REQ 10: Work with different queueing systems
--------------------------------------------

The current collector has several queuing classes.

We want the new collector to have the following:

1. a null queueing class that is a no-op and is the default out of the box: it
   should log a single line per crash queued for processing
2. a RabbitMQ class

.. todo:: Anything else? Do we want a Postgres based one?


REQ 11: Support non-breakpad crash reports
------------------------------------------

Should handle Raven-created reports and Breakpad-created reports.

The current collector has a generic crash collector in addition to the breakpad
one. The generic collector removes ``\00`` characters from incoming crash
reports.




Implementation decisions
========================

FIXME: These are up in the air!


Which framework?
----------------

Things we might want (FIXME!):

* Works on Heroku.
* Doesn't require a db.
* Minimal dependencies.
* Event loop is probably helpful.
* WSGI compliant?
* Good documentation.
* Mature.
* Minimal footprint.
* Minimal magic.
* Good throughput.
* Used at Mozilla?

.. todo:: What other things should we be looking for?

Possibilities:

* gunicorn + flask + gevent
* cherrypy + gevent ?
* gunicorn + falcon + gevent
* tornado ?
* twisted ?

.. todo:: Others that are compelling to look at?

.. todo:: Works on heroku?


Should we use configman for configuration?
------------------------------------------

I kind of think we should stick with it unless there's a compelling reason not
to.

Also note that if we use the configman library, that doesn't require us to use
the same infrasturcture for mocularizing components that socorro currently uses.

If we go with configman, I want to do a better job of modularizing configman
components--I think this is causing most of the problems we have.

.. todo:: Read through configman more.


Should we use socorro or socorrolib?
------------------------------------

"No" until we have to say "Yes".

If I have my druthers, the collector will be entirely self-contained and won't
depend on or import anything from socorro or socorrolib.


How to deal with s3 availability issues?
----------------------------------------

.. todo:: Figure this out.


How to deal with queue availability issues?
-------------------------------------------

.. todo:: Figure this out.


Implementation plan
===================

FIXME: This is up in the air!
