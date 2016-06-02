# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_, ok_

from collector.external.fs.fs_new_crash_source import (
    FSNewCrashSource
)
from collector.lib.util import DotDict
from collector.unittest.testbase import TestCase


#==============================================================================
class FakeCrashStore(object):

    def __init__(self, config, quit_check):
        self.config = config
        self.quit_check = quit_check

    def new_crashes(self):
        for a_crash_id in range(10):
            yield str(a_crash_id)

    def ack_crash(self, crash_id):
        return crash_id


#==============================================================================
class TestConnection(TestCase):
    """Test FSNewCrashSource class. """

    #--------------------------------------------------------------------------
    def _setup_config(self):
        config = DotDict();
        config.crashstorage_class = FakeCrashStore
        return config

    #--------------------------------------------------------------------------
    def test_constructor(self):
        config = self._setup_config()
        ncs = FSNewCrashSource(config, name="ignored_processor_name")
        ok_(isinstance(ncs.crash_store, FakeCrashStore))
        ok_(ncs.crash_store.config is config)

    #--------------------------------------------------------------------------
    def test__iter__(self):
        config = self._setup_config()
        ncs = FSNewCrashSource(config)
        for i, (args, kwargs) in zip(range(10), ncs()):
            crash_id = args[0]
            eq_(str(i), crash_id)
            eq_(kwargs, {})
        eq_(i, 9)
