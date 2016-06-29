========================
Crash storage: Boto (S3)
========================

Crash storage
=============

.. autoconfigman:: collector.external.boto.crashstorage.BotoS3CrashStorage


Connection contexts
===================

.. autoconfigman:: collector.external.boto.connection_context.ConnectionContextBase

.. autoconfigman:: collector.external.boto.connection_context.S3ConnectionContext

.. autoconfigman:: collector.external.boto.connection_context.RegionalS3ConnectionContext

.. autoconfigman:: collector.external.boto.connection_context.HostPortS3ConnectionContext


Key builders
============

.. autoconfigman:: collector.external.boto.connection_context.KeyBuilderBase

.. autoconfigman:: collector.external.boto.connection_context.DatePrefixKeyBuilder
