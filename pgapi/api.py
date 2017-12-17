#!/usr/bin/env python3

import sys
import logging
import argparse

sys.path.append('.')

from pgapi.helper import Config
from pgapi.server import ServerAPI

logging.basicConfig(level=logging.WARNING)

# Config Setup
config = Config.getInstance()

# Argument parsing
parser = argparse.ArgumentParser(description="PostgreSQL API")
parser.add_argument("--config-file", type=str)
parser.add_argument("--name", type=str)
parser.add_argument("--port", type=int)
parser.add_argument("--listen_address", type=str)
parser.add_argument("--use_sudo", type=bool)
parser.add_argument("--sudo_user", type=str)
parser.add_argument("--bypass_systemd", type=bool)
parser.add_argument("--ssl_mode", type=str)
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

# Load Config file, if given
if args.config_file is not None:
    config.loadConfigFile(args.config_file)

# Save command line arguments in runtime config
for arg in vars(args):
    value = getattr(args, arg)
    if value is not None:
        logging.debug("Save command line argument \"%s\" with value \"%s\"",
                      arg, value)
        config.setSetting("arguments", arg, value)

if config.getSetting("debug"):
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("debugging enabled")

# Setup API Server
server = ServerAPI()
server.setup(config)
server.start()
