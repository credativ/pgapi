#!/usr/bin/env python

import os
import re
import sys
import subprocess
import json
import logging
import traceback
import shutil
import time

from pgapi import helper

CTL_ALLOWED_ACTIONS = ["start", "stop", "restart", "reload", "promote", "status"]


def _json_loads_wrapper(string, command='unnamed command'):
    try:
        _json = json.loads(string)
    except Exception as e:
        logging.error( "%s::%s"%( command, e ) )
        # Something broke around here. We'll catch the error to provide a stable api.
        # To allow for some debugging, we'll print the stacktrace anyhow.
        logging.error( traceback.print_exc() )
        raise Exception("%s output is not valid json."%(command) )
    return _json

def _error_to_json( message ):
    error=dict()
    error['Error'] = str(message)
    return json.dumps(error)


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
    As commandoutput will always be reinterpreted we'll ensure maximum compatibility
    via LC_ALL=C.
    Commands should always be transmitted as an array to ensure security.
    However, it is possible to injext a string for compatibility reasons.
    """
    if isinstance( command, str ): # Compat
        command = command.split()

    logging.debug("request to execute \"%s\"", command)
    subprocess_env = dict( os.environ )
    subprocess_env['LC_ALL'] = 'C'

    # get system encoding
    config = helper.Config.getInstance()
    encoding = config.getSetting("encoding")
    
    # prefix with sudo and locale
    command = sudo_prefix().split() +  command
    logging.info("execute command \"%s\"", command)
    try:
        ## As of python 3.6, 'encoding' is a valid argument for subprocess.
        ## To achieve compatibility to earlier versions of python we refrain from it.
        proc = subprocess.Popen( command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=subprocess_env )
        (stdout, stderr) = proc.communicate()
        (stdout, stderr) = (stdout.decode( encoding ), stderr.decode( encoding ) )
    except Exception as e:
        logging.error("Execution of %s failed"%(command) )
        logging.error(e)
        traceback.print_exc()
        raise e
    returncode = proc.returncode
    logging.debug("command retured (%d) stdout: \"%s\" stderr: \"%s\"", returncode, stdout, stderr)

    return (returncode, stdout, stderr)

def cluster_ctl(version, name, action):
    """Control a existing cluster.
    """
    if not action in CTL_ALLOWED_ACTIONS:
        raise Exception("Action has to be one of %s" % (str(CTL_ALLOWED_ACTIONS ) ))

    config = helper.Config.getInstance()

    options = ""
    if action in ["stop", "restart"]:
        options = "-f"

    sudo = ""
    if config.getSetting("bypass_systemd") is False:
        sudo = "sudo "

    (returncode, stdout, stderr) = _run_command('{}pg_ctlcluster {} {} {} {}'.format(sudo, version, name, action, options))
    return (returncode, stdout, stderr)

def SR_create( version, name, conninfo ):
    # To create a streaming_standby, a created cluster is required.
    # This makes sure all configuration settings are in place and as required.
    # Syncing configuration with the primary can be done with additional API-calls if required.
    # The created clusters data-directory contents will be purged. pg_basebackup will be used to fill
    # said directory.

    # TODO: Replication_Slots

    infos=cluster_get(version, name)
    pgdata=infos[0]['pgdata']
    # Deleting an instance seems dangerous. Lets put as much effort into
    # making sure we don't delete anything as possible.
    assert( os.path.exists ( os.path.join(pgdata,'base'))  )                     # There should be the heap-directory within the datadir.
    assert( os.path.exists ( os.path.join(pgdata,'postmaster.pid'))==False )    # The directory should've just been created. No pid is expected.
    assert( time.time()                                                         # Racy assumption that the PG_VERSION tag within the target datadir
            - os.stat(                                                          # is less than 60Seconds old.
                os.path.join(pgdata,'PG_VERSION')                               # PG_VERSION should rarely ever be updated, hence it is a good
                ).st_ctime                                                      # safeguard.
            < 60 ) 

    shutil.rmtree( pgdata )
    basebackup=["pg_basebackup",
                "-Xfetch",
                "-d",
                conninfo,
                "-D",
                pgdata,
                "--write-recovery-conf",
                "--checkpoint=fast"
                ]
    (returncode, stdout, stderr) = _run_command(basebackup)
    return (returncode, stderr)

def cluster_create(version, name, opts=None):
    """Creates a new cluster.
    """

    # To create a cluster we need to provide an interface to exactly two programs.
    # pg_createcluster and initdb.

    # As arguments for both are finite and do not overlap, we'll split them here into
    # two arrays. Specialcasing where appropriate.

    cmd = ["pg_createcluster",
            version,
            name]
    initdbOpts = []
    sr_conninfo = None
    if opts is not None:
        for key, value in opts.items():
            if value is None:
                # Argparse will provide arguments. We don't need to present those to the
                # programs, so we'll skip
                continue
            if key == 'data-checksums':
                initdbOpts += ['--data-checksums',]
            elif key == 'primary_conninfo':
                sr_conninfo = value
            else:
                cmd += ['--%s=%s' % (key, value), ]

    (returncode, stdout, stderr) = _run_command( cmd + ['--',] + initdbOpts )

    # IFF the cluster was successfully created and an SR_Standby was required,
    # the data-dir of said instance can be purged.
    # This could cause data loss if pg_createcluster returns OK against existing clusters.
    if sr_conninfo != None and returncode == 0:
        # If SR_create fails, an error will be reported. For now there is no automatic cleanup.
        # This tends to be a good idea as it allows the user to investigate the error.
        (rc,err) = SR_create( version, name, sr_conninfo)
        returncode=rc
        stderr+=err

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

def pgcontroldata_get ( pgdata, version ):
    returndict = {}
    assert( os.path.exists ( pgdata ) )
    # PostgreSQL should not be shipped without pg_controldata. Hence it is sane
    # to check for the version. Could fail on minimalistic installations.

    # It should be save to assume that whatever binary a data-directory needs is 
    # installed to the system and has a binary_path.
    binarypath = helper.get_installed_postgresql_versions()[version]['binary_path']
    controldata= os.path.join( binarypath, 'pg_controldata' )

    # It could be a symlink and we keep it simple. Check for existence
    assert(os.path.exists ( controldata ) )

    command = '%s %s'%(controldata, pgdata )
    # This call is quite likely to fail as it raises the required Permissions to pgdata-owner
    # or root.
    (returncode, stdout, stderr) = _run_command( command )
    if returncode != 0:
        raise Exception(stderr)
    stdout=stdout.split('\n')

    # pg_controldata adds error-messages. We'll omit those for now.
    stdout=[ line for line in stdout if ': ' in line ]

    stdout=[ line.split(': ') for line in stdout ]

    for line in stdout:
        returndict[line[0]]=line[1].lstrip()
    return returndict


def cluster_get_all():
    """Returns a list of all clusters in as python list.
    """
    command = 'pg_lsclusters --json'
    (returncode, stdout, stderr) = _run_command( command )

    if returncode != 0:
        logging.error("Clusterlisting reports an error. %s"%( stderr.strip() ) )
    try:
        if stdout == '':
            raise
        clusters = _json_loads_wrapper(stdout,command) #Critical section. Likely to raise errors
    except Exception as e:
        return _error_to_json( e )

    for cluster in clusters:
        try:
            cluster['pg_controldata']=pgcontroldata_get( cluster['pgdata'], cluster['version'] )
        except Exception as e:
            # pgcontroldata requires a lot more permissions than pg_lsclusters.
            # For that matter an error will be reported, but the call will not fail entirely.
            cluster['pg_controldata']='Unavailable. %s'%(e)
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
