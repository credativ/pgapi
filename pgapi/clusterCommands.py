#!/usr/bin/env python

import sys
import subprocess
import json
import logging

from pgapi import helper

CTL_ALLOWED_ACTIONS = ["start", "stop", "restart", "reload", "promote", "status"]

def sudo_prefix():
    """returns a sudo prefix
    if use_sudo _and_ sudo user is defined
    overwise emptystring
    """
    config = helper.Config.getInstance()
    use_sudo = config.getSetting("use_sudo")
    sudo_user = config.getSetting("sudo_user")

    if use_sudo and sudo_user:
        return "sudo -u {}".format(sudo_user)

    return ""

def _run_command(command):
    """Run a give command.
    The command is check against a specific regex to ensure it's safe
    to execute. See command_is_safe().
    """
    logging.debug("request to execute \"%s\"", command)
    # forbid unsafe commands. This one needs some love.
    if not helper.command_is_safe(command):
        logging.error("denail to execute command \"%s\". It's considered unsave.", command)
        raise 'command not safe'

    # get system encoding
    config = helper.Config.getInstance()
    encoding = config.getSetting("encoding")
    
    # prefix with sudo
    command = "{} {}".format(sudo_prefix(), command)
    logging.info("execute command \"%s\"", command)

    proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding=encoding)
    (stdout, stderr) = proc.communicate()
    returncode = proc.returncode
    logging.debug("command retured (%d) stdout: \"%s\" stderr: \"%s\"", returncode, stdout, stderr)

    return (returncode, stdout, stderr)

def cluster_ctl(version, name, action):
    """Control a existing cluster.
    """
    if not action in CTL_ALLOWED_ACTIONS:
        raise "Action has to be one of %s" % allowed_actions

    config = helper.Config.getInstance()

    options = ""
    if action in ["stop", "restart"]:
        options == "-f"

    sudo = ""
    if config.getSetting("bypass_systemd") is False:
        sudo = "sudo "

    (returncode, stdout, stderr) = _run_command('{}pg_ctlcluster {} {} {} {}'.format(sudo, version, name, action, options))
    return (returncode, stdout, stderr)

def cluster_create(version, name, opts=None):
    """Creates a new cluster.
    """
    cmd = 'pg_createcluster %s %s' % (version, name)

    if opts is not None:
        for key, value in opts.iteritems():
            cmd += ' --%s=%s' % (key, value)

    (returncode, stdout, stderr) = _run_command(cmd)
    return (returncode, stdout, stderr)

def cluster_drop(version, name):
    """Drops a existing cluster.
    """
    cmd = 'pg_dropcluster %s %s' % (version, name)
    (returncode, stdout, stderr) = _run_command(cmd)
    return (returncode, stdout, stderr)

def cluster_get_setting(version, name, setting):
    cmd = '/usr/bin/pg_conftool --short %s %s show %s' % (version, name, setting)
    (returncode, stdout, stderr) = _run_command(cmd)
    if returncode != 0:
        return None

    return stdout.strip()

def cluster_set_setting(version, name, setting, value):
    """Changes the value of a existing cluster.
    """
    cmd = '/usr/bin/pg_conftool --short %s %s set %s %s' % (version, name, setting, value)
    return _run_command(cmd)

def cluster_get_all():
    """Returns a list of all clusters in as python list.
    """
    (returncode, stdout, stderr) = _run_command('pg_lsclusters --json')

    if returncode != 0:
        print("Could not get Clusters")

    clusters = json.loads(stdout)
    return clusters

def cluster_get(version=None, name=None):
    """Returns a specific cluster as python dict.
    """
    clusters = cluster_get_all()

    # Filter version and name
    if not version is None:
        clusters = [c for c in clusters if c["version"] == version]
    if not name is None:
        clusters = [c for c in clusters if c["cluster"] == name]

    return clusters
