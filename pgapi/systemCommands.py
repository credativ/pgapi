#!/usr/bin/env python

import os
import json
import logging
import socket
import psutil

from pgapi import helper

def get_system_info(section=None):
    """Get global system information.

       Returns a dictionary that contains various sections about
       system specific sections. See sections variable for a complete
       list.
    """
    system_info = {}

    sections = {
        "hostname": get_hostname,
        "uname": get_uname,
        "installed_pg_versions": get_installed_postgresql_versions,
        "cpu_config": get_cpu_config,
        "disk_partitions": get_disk_partitions,
        "disk_usage": get_disk_usage,
        "virtual_memory": get_virtual_memory,
        "swap_memory": get_swap_memory,
        "load": get_load,
    }

    if section is None:
        for name, function_ref in sections.items():
            logging.debug("Evaluate function_ref for \"%s\"", name)
            system_info[name] = function_ref()

    if section in sections.keys():
        logging.debug("Evaluate function_ref for \"%s\"", section)
        system_info[section] = sections[section]()

    return system_info


def get_hostname():
    hostname = {}

    hostname["hostname"] = socket.gethostname()
    hostname["fqdn"] = socket.getfqdn()

    return hostname


def get_uname():
    (kernel_name, nodename, kernel_release, kernel_version, machine) = os.uname()

    uname = {"kernel_name": kernel_name,
             "nodename": nodename,
             "kernel_release": kernel_release,
             "kernel_version": kernel_version,
             "machine": machine
             }
    return uname


def get_installed_postgresql_versions():
    return helper.get_installed_postgresql_versions()


def get_cpu_config():
    cpu_config = {}

    cpu_config["cpu_count"] = psutil.cpu_count(logical=False)
    cpu_config["cpu_count_logical"] = psutil.cpu_count(logical=True)

    return cpu_config


def get_disk_partitions():
    disk_partitions = psutil.disk_partitions()

    return disk_partitions


def _get_mount_points():
    mount_points = [x.mountpoint for x in psutil.disk_partitions()]

    return mount_points


def _get_disk_usage_single_mountpoint(mountpoint):
    return psutil.disk_usage(mountpoint)


def get_disk_usage():
    mount_points = _get_mount_points()
    disk_usage = {}

    for mount in mount_points:
        disk_usage[mount] = psutil.disk_usage(mount)

    return disk_usage


def get_virtual_memory():
    return psutil.virtual_memory()


def get_swap_memory():
    return psutil.swap_memory()


def get_load():
    (load_1min, load_5min, load_15min) = os.getloadavg()

    load = {"1min": load_1min,
            "5min": load_5min,
            "15min": load_15min
            }
    return load
