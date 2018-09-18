#!/usr/bin/env python

import os
import sys
import subprocess
import json
import logging
import traceback
import socket

from pgapi import helper

def get_system_info():
    system_info = {}

    system_info["hostname"] = get_hostname()
    system_info["uname"] = get_uname()
    system_info["installed_pg_versions"] = get_installed_postgresql_versions()

    return system_info
    
def get_hostname():
    hostname = {}

    hostname["hostname"] = socket.gethostname()
    hostname["fqdn"] = socket.getfqdn()
    
    return hostname

def get_uname():
    return os.uname()

def get_installed_postgresql_versions():
    versions = {}
    install_dir = "/usr/lib/postgresql/"

    subdirs = os.listdir(install_dir)

    for version_dir in subdirs:
        initdb_path = os.path.join(*[install_dir, version_dir, "bin", "initdb"])
        if os.path.isfile(initdb_path):
            # TODO fill up hash with version details
            versions[version_dir] = {}

    return subdirs
