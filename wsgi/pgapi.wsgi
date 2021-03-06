#!/usr/bin/env python3

import sys
import logging
import argparse

from pgapi.helper import Config
from pgapi.server import ServerAPI

logging.basicConfig(level=logging.WARNING)

# Config Setup
config = Config.getInstance()

if config.loadConfigFile(config.getSetting("config_file")) is not True:
    logging.warning("Cloud not load config file \"%s\"", config.getSetting("config_file"))

if config.getSetting("debug"):
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("debugging enabled")

# Setup API Server
server = ServerAPI()
(application, api) = server.setup(config)
