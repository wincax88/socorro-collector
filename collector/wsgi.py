# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from collector.app.socorro_app import (
    SocorroWelcomeApp,
    main
)
from collector.webapi.servers import WSGIServer
import collector.collector_app

from configman import (
    ConfigFileFutureProxy,
    environment
)

if os.path.isfile('/etc/socorro/collector.ini'):
    config_path = '/etc/socorro'
else:
    config_path = WSGIServer.get_socorro_config_path(__file__)

# invoke the generic main function to create the configman app class and which
# will then create the wsgi app object.
main(
    # We use the generic Socorro App class. We'll rely on configuration to set
    # the 'application' class object to the appropriate collector_app class.
    # For example, it could be "CollectorApp".
    SocorroWelcomeApp,
    config_path=config_path,
    values_source_list=[
        ConfigFileFutureProxy,
        environment
    ]
)

application = collector.collector_app.application
