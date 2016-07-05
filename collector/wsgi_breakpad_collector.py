# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from collector.lib.ooid import createNewOoid
from collector.throttler import DISCARD, IGNORE
from collector.lib.datetimeutil import utc_now
from collector.wsgi_generic_collector import GenericCollectorBase

from configman import Namespace


#==============================================================================
class BreakpadCollector(GenericCollectorBase):
    #--------------------------------------------------------------------------
    # in this section, define any configuration requirements
    required_config = Namespace()
    required_config.add_option(
        'dump_field',
        doc='the name of the form field containing the raw dump',
        default='upload_file_minidump'
    )
    required_config.add_option(
        'dump_id_prefix',
        doc='the prefix to return to the client in front of the OOID',
        default='bp-'
    )
    required_config.add_option(
        'accept_submitted_legacy_processing',
        doc='a boolean telling the collector to use a any legacy_processing'
            'flag submitted with the crash',
        default=False
    )

    uri = '/submit'

    #--------------------------------------------------------------------------
    def __init__(self, config):
        super(BreakpadCollector, self).__init__(config)
        self.dump_field = self._get_dump_field()
        self.dump_id_prefix = self._get_dump_id_prefix()
        self.accept_submitted_legacy_processing = \
            self._get_accept_submitted_legacy_processing()
        self.throttler = self._get_throttler()
        self.crash_storage = self._get_crash_storage()

    #--------------------------------------------------------------------------
    def _get_crash_storage(self):
        return self.config.crash_storage

    #--------------------------------------------------------------------------
    def POST(self, *args):
        raw_crash, dumps = self._get_raw_crash_from_form()

        current_timestamp = utc_now()
        raw_crash.submitted_timestamp = current_timestamp.isoformat()
        # legacy - ought to be removed someday
        raw_crash.timestamp = time.time()

        if (not self.accept_submitted_crash_id or 'uuid' not in raw_crash):
            crash_id = createNewOoid(current_timestamp)
            raw_crash.uuid = crash_id
            self.logger.info('%s received', crash_id)
        else:
            crash_id = raw_crash.uuid
            self.logger.info('%s received with existing crash_id:', crash_id)

        if ('legacy_processing' not in raw_crash
            or not self.accept_submitted_legacy_processing
        ):
            raw_crash.legacy_processing, raw_crash.throttle_rate = (
                self.throttler.throttle(raw_crash)
            )
        else:
            raw_crash.legacy_processing = int(raw_crash.legacy_processing)

        if raw_crash.legacy_processing == DISCARD:
            self.logger.info('%s discarded', crash_id)
            return "Discarded=1\n"
        if raw_crash.legacy_processing == IGNORE:
            self.logger.info('%s ignored', crash_id)
            return "Unsupported=1\n"

        raw_crash.type_tag = self.dump_id_prefix.strip('-')

        self.crash_storage.save_raw_crash(
            raw_crash,
            dumps,
            crash_id
        )
        self.logger.info('%s accepted', crash_id)
        return "CrashID=%s%s\n" % (self.dump_id_prefix, crash_id)

    #--------------------------------------------------------------------------
    def _get_throttler(self):
        return self.config.throttler

    #--------------------------------------------------------------------------
    def _get_dump_field(self):
        return self.config.collector.dump_field

    #--------------------------------------------------------------------------
    def _get_dump_id_prefix(self):
        return self.config.collector.dump_id_prefix

    #--------------------------------------------------------------------------
    def _get_accept_submitted_legacy_processing(self):
        return self.config.collector.accept_submitted_legacy_processing

    #--------------------------------------------------------------------------
    def _get_checksum_method(self):
        return self.config.collector.checksum_method

    #--------------------------------------------------------------------------
    def _get_accept_submitted_crash_id(self):
        return self.config.collector.accept_submitted_crash_id
