# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import socket

from nose.tools import eq_, ok_, assert_raises
from configman import Namespace, ConfigurationManager, class_converter, RequiredConfig
import collector.database.transaction_executor
from collector.database.transaction_executor import (
  TransactionExecutor, TransactionExecutorWithInfiniteBackoff)
from collector.unittest.testbase import TestCase


# From psycopg2.
TRANSACTION_STATUS_IDLE = 0
TRANSACTION_STATUS_INTRANS = 2
class OperationalError(Exception): pass
class ProgrammingError(Exception): pass
class InterfaceError(Exception): pass


class SomeError(Exception):
    pass


class MockConnectionContext(RequiredConfig):
    """Minimum viable connection context class

    Note: In socorro, this test module uses the postgres external connection
    class for testing. We're not pulling in any postgres anything into
    socorro-collector, so we implement this class as a mock version of the
    postgres connection context.

    """
    required_config = Namespace()

    def __init__(self, config, local_config=None):
        self.config = config
        self.operational_exceptions = (
            InterfaceError,
            socket.timeout,
        )
        self.conditional_exceptions = (
            OperationalError,
            ProgrammingError,
        )

    def connection(self, __=None):
        return MockConnection()
 
    def close_connection(self, connection, force=False):
        connection.close()

    @contextlib.contextmanager
    def __call__(self, name=None):
        conn = self.connection(name)
        try:
            yield conn
        finally:
            self.close_connection(conn)

    def is_operational_exception(self, exp):
        """return True if a conditional exception is actually an operational
        error. Return False if it's a genuine error that should probably be
        raised and propagate up.

        Some conditional exceptions might be actually be some form of
        operational exception "labelled" wrong by the psycopg2 code error
        handler.
        """
        message = exp.args[0]
        if message in ('SSL SYSCALL error: EOF detected', ):
            # Ideally we'd like to check against exp.pgcode values
            # but certain odd ProgrammingError exceptions don't have
            # pgcodes so we have to rely on reading the pgerror :(
            return True

        if (
            isinstance(exp, OperationalError) and
            message not in ('out of memory',)
        ):
            return True

        # at the of writing, the list of exceptions is short but this would be
        # where you add more as you discover more odd cases of psycopg2

        return False

    def force_reconnect(self):
        pass


class MockLogging:
    def __init__(self):
        self.debugs = []
        self.warnings = []
        self.errors = []
        self.criticals = []

    def debug(self, *args, **kwargs):
        self.debugs.append((args, kwargs))

    def warning(self, *args, **kwargs):
        self.warnings.append((args, kwargs))

    def error(self, *args, **kwargs):
        self.errors.append((args, kwargs))

    def critical(self, *args, **kwargs):
        self.criticals.append((args, kwargs))


class MockConnection(object):

    def __init__(self):
        self.transaction_status = TRANSACTION_STATUS_IDLE

    def get_transaction_status(self):
        return self.transaction_status

    def close(self):
        pass

    def commit(self):
        global commit_count
        commit_count += 1

    def rollback(self):
        global rollback_count
        rollback_count += 1


commit_count = 0
rollback_count = 0


class TestTransactionExecutor(TestCase):

    def setUp(self):
        global commit_count, rollback_count
        commit_count = 0
        rollback_count = 0

    def test_basic_usage_with_postgres(self):
        required_config = Namespace()
        required_config.add_option(
          'transaction_executor_class',
          #default=TransactionExecutorWithBackoff,
          default=TransactionExecutor,
          doc='a class that will execute transactions'
        )
        required_config.add_option(
          'database_class',
          default=MockConnectionContext,
          from_string_converter=class_converter
        )
        mock_logging = MockLogging()
        required_config.add_option('logger', default=mock_logging)

        config_manager = ConfigurationManager(
          [required_config],
          app_name='testapp',
          app_version='1.0',
          app_description='app description',
          values_source_list=[],
          argv_source=[]
        )
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(config,
                                                         mocked_context)
            _function_calls = []  # some mutable

            def mock_function(connection):
                assert isinstance(connection, MockConnection)
                _function_calls.append(connection)

            executor(mock_function)
            ok_(_function_calls)
            eq_(commit_count, 1)
            eq_(rollback_count, 0)

    def test_rollback_transaction_exceptions_with_postgres(self):
        required_config = Namespace()
        required_config.add_option(
          'transaction_executor_class',
          default=TransactionExecutor,
          doc='a class that will execute transactions'
        )
        required_config.add_option(
          'database_class',
          default=MockConnectionContext,
          from_string_converter=class_converter
        )

        mock_logging = MockLogging()
        required_config.add_option('logger', default=mock_logging)

        config_manager = ConfigurationManager(
          [required_config],
          app_name='testapp',
          app_version='1.0',
          app_description='app description',
          values_source_list=[],
          argv_source=[]
        )
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(config,
                                                         mocked_context)

            def mock_function(connection):
                assert isinstance(connection, MockConnection)
                connection.transaction_status = TRANSACTION_STATUS_INTRANS
                raise SomeError('crap!')

            assert_raises(SomeError, executor, mock_function)

            eq_(commit_count, 0)
            eq_(rollback_count, 1)
            ok_(mock_logging.errors)

    def test_basic_usage_with_postgres_with_backoff(self):
        required_config = Namespace()
        required_config.add_option(
          'transaction_executor_class',
          default=TransactionExecutorWithInfiniteBackoff,
          #default=TransactionExecutor,
          doc='a class that will execute transactions'
        )
        required_config.add_option(
          'database_class',
          default=MockConnectionContext,
          from_string_converter=class_converter
        )

        config_manager = ConfigurationManager(
          [required_config],
          app_name='testapp',
          app_version='1.0',
          app_description='app description',
          values_source_list=[],
          argv_source=[]
        )
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(config,
                                                         mocked_context)
            _function_calls = []  # some mutable

            def mock_function(connection):
                assert isinstance(connection, MockConnection)
                _function_calls.append(connection)

            executor(mock_function)
            ok_(_function_calls)
            eq_(commit_count, 1)
            eq_(rollback_count, 0)

    def test_operation_error_with_postgres_with_backoff(self):
        required_config = Namespace()
        required_config.add_option(
          'transaction_executor_class',
          default=TransactionExecutorWithInfiniteBackoff,
          #default=TransactionExecutor,
          doc='a class that will execute transactions'
        )
        required_config.add_option(
          'database_class',
          default=MockConnectionContext,
          from_string_converter=class_converter
        )

        mock_logging = MockLogging()
        required_config.add_option('logger', default=mock_logging)

        config_manager = ConfigurationManager(
          [required_config],
          app_name='testapp',
          app_version='1.0',
          app_description='app description',
          values_source_list=[{'backoff_delays': [2, 4, 6, 10, 15]}],
          argv_source=[]
        )
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(config,
                                                         mocked_context)
            _function_calls = []  # some mutable

            _sleep_count = []

            def mock_function(connection):
                assert isinstance(connection, MockConnection)
                _function_calls.append(connection)
                # the default sleep times are going to be,
                # 2, 4, 6, 10, 15
                # so after 2 + 4 + 6 + 10 + 15 seconds
                # all will be exhausted
                if sum(_sleep_count) < sum([2, 4, 6, 10, 15]):
                    raise OperationalError('Arh!')

            def mock_sleep(n):
                _sleep_count.append(n)

            # monkey patch the sleep function from inside transaction_executor
            _orig_sleep = collector.database.transaction_executor.time.sleep
            collector.database.transaction_executor.time.sleep = mock_sleep

            try:
                executor(mock_function)
                ok_(_function_calls)
                eq_(commit_count, 1)
                eq_(rollback_count, 5)
                ok_(mock_logging.criticals)
                eq_(len(mock_logging.criticals), 5)
                ok_(len(_sleep_count) > 10)
            finally:
                collector.database.transaction_executor.time.sleep = _orig_sleep

    def test_operation_error_with_postgres_with_backoff_with_rollback(self):
        required_config = Namespace()
        required_config.add_option(
          'transaction_executor_class',
          default=TransactionExecutorWithInfiniteBackoff,
          #default=TransactionExecutor,
          doc='a class that will execute transactions'
        )
        required_config.add_option(
          'database_class',
          default=MockConnectionContext,
          from_string_converter=class_converter
        )

        mock_logging = MockLogging()
        required_config.add_option('logger', default=mock_logging)

        config_manager = ConfigurationManager(
          [required_config],
          app_name='testapp',
          app_version='1.0',
          app_description='app description',
          values_source_list=[{'backoff_delays': [2, 4, 6, 10, 15]}],
          argv_source=[]
        )
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(config,
                                                         mocked_context)
            _function_calls = []  # some mutable

            _sleep_count = []

            def mock_function(connection):
                assert isinstance(connection, MockConnection)
                connection.transaction_status = TRANSACTION_STATUS_INTRANS
                _function_calls.append(connection)
                # the default sleep times are going to be,
                # 2, 4, 6, 10, 15
                # so after 2 + 4 + 6 + 10 + 15 seconds
                # all will be exhausted
                if sum(_sleep_count) < sum([2, 4, 6, 10, 15]):
                    raise OperationalError('Arh!')

            def mock_sleep(n):
                _sleep_count.append(n)

            # monkey patch the sleep function from inside transaction_executor
            _orig_sleep = collector.database.transaction_executor.time.sleep
            collector.database.transaction_executor.time.sleep = mock_sleep

            try:
                executor(mock_function)
                ok_(_function_calls)
                eq_(commit_count, 1)
                eq_(rollback_count, 5)
                ok_(mock_logging.criticals)
                eq_(len(mock_logging.criticals), 5)
                ok_(len(_sleep_count) > 10)
            finally:
                collector.database.transaction_executor.time.sleep = _orig_sleep

    def test_programming_error_with_postgres_with_backoff_with_rollback(self):
        required_config = Namespace()
        required_config.add_option(
          'transaction_executor_class',
          default=TransactionExecutorWithInfiniteBackoff,
          doc='a class that will execute transactions'
        )
        required_config.add_option(
          'database_class',
          default=MockConnectionContext,
          from_string_converter=class_converter
        )

        mock_logging = MockLogging()
        required_config.add_option('logger', default=mock_logging)

        config_manager = ConfigurationManager(
          [required_config],
          app_name='testapp',
          app_version='1.0',
          app_description='app description',
          values_source_list=[{'backoff_delays': [2, 4, 6, 10, 15]}],
          argv_source=[]
        )
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(config,
                                                         mocked_context)
            _function_calls = []  # some mutable

            _sleep_count = []

            def mock_function_struggling(connection):
                assert isinstance(connection, MockConnection)
                connection.transaction_status = TRANSACTION_STATUS_INTRANS
                _function_calls.append(connection)
                # the default sleep times are going to be,
                # 2, 4, 6, 10, 15
                # so after 2 + 4 + 6 + 10 + 15 seconds
                # all will be exhausted
                if sum(_sleep_count) < sum([2, 4, 6, 10, 15]):
                    raise ProgrammingError(
                        'SSL SYSCALL error: EOF detected'
                    )

            def mock_sleep(n):
                _sleep_count.append(n)

            # monkey patch the sleep function from inside transaction_executor
            _orig_sleep = collector.database.transaction_executor.time.sleep
            collector.database.transaction_executor.time.sleep = mock_sleep

            try:
                executor(mock_function_struggling)
                ok_(_function_calls)
                eq_(commit_count, 1)
                eq_(rollback_count, 5)
                ok_(mock_logging.criticals)
                eq_(len(mock_logging.criticals), 5)
                ok_(len(_sleep_count) > 10)
            finally:
                collector.database.transaction_executor.time.sleep = _orig_sleep

        # this time, simulate an actual code bug where a callable function
        # raises a ProgrammingError() exception by, for example, a syntax error
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(config,
                                                         mocked_context)

            def mock_function_developer_mistake(connection):
                assert isinstance(connection, MockConnection)
                connection.transaction_status = TRANSACTION_STATUS_INTRANS
                raise ProgrammingError("syntax error")

            assert_raises(ProgrammingError,
                              executor,
                              mock_function_developer_mistake)

    def test_abandon_transaction(self):
        """this is when a transaction is intentionally aborted, not because
        of an error, but because the client of the TransactionExcutor has
        determined that the transaction is of no further use."""
        required_config = Namespace()
        required_config.add_option(
          'transaction_executor_class',
          default=TransactionExecutor,
          doc='a class that will execute transactions'
        )
        required_config.add_option(
          'database_class',
          default=MockConnectionContext,
          from_string_converter=class_converter
        )

        mock_logging = MockLogging()
        required_config.add_option('logger', default=mock_logging)

        config_manager = ConfigurationManager(
          [required_config],
          app_name='testapp',
          app_version='1.0',
          app_description='app description',
          values_source_list=[],
          argv_source=[]
        )
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(
                config,
                mocked_context
            )

            class AbandonTransaction(Exception):
                abandon_transaction = True

            def mock_function(connection):
                assert isinstance(connection, MockConnection)
                connection.transaction_status = TRANSACTION_STATUS_INTRANS
                raise AbandonTransaction('crap!')

            # the method to test
            executor(mock_function)

            eq_(commit_count, 0)
            eq_(rollback_count, 1)
            ok_(not mock_logging.errors)

    def test_abandon_backoff_transaction(self):
        """this is when a transaction is intentionally aborted, not because
        of an error, but because the client of the TransactionExcutor has
        determined that the transaction is of no further use.  This test
        uses the TransactionExecutorWithInfiniteBackoff class instead of
        the base TransactionExcutor"""
        required_config = Namespace()
        required_config.add_option(
          'transaction_executor_class',
          default=TransactionExecutorWithInfiniteBackoff,
          doc='a class that will execute transactions'
        )
        required_config.add_option(
          'database_class',
          default=MockConnectionContext,
          from_string_converter=class_converter
        )

        mock_logging = MockLogging()
        required_config.add_option('logger', default=mock_logging)

        config_manager = ConfigurationManager(
          [required_config],
          app_name='testapp',
          app_version='1.0',
          app_description='app description',
          values_source_list=[],
          argv_source=[]
        )
        with config_manager.context() as config:
            mocked_context = config.database_class(config)
            executor = config.transaction_executor_class(
                config,
                mocked_context
            )

            class AbandonTransaction(Exception):
                abandon_transaction = True

            def mock_function(connection):
                assert isinstance(connection, MockConnection)
                connection.transaction_status = TRANSACTION_STATUS_INTRANS
                raise AbandonTransaction('crap!')

            # the method to test
            executor(mock_function)

            eq_(commit_count, 0)
            eq_(rollback_count, 1)
            ok_(not mock_logging.errors)
