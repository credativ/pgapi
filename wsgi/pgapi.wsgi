#!/usr/bin/env python3

import logging

from pgapi.server import ServerAPI

logging.basicConfig(level=logging.WARNING)

# Setup API Server
server = ServerAPI()
(application, api) = server.setup()
