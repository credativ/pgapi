from subprocess import Popen, PIPE
from logging import warning, debug
from pathlib import Path
import os

from threading import Thread
from collections import deque
import json
import uuid
import time
import datetime

from configparser import ConfigParser, DuplicateSectionError
import pgapi.clusterCommands as cc

class cli_output():
    def __init__(self, stdout=None, stderr=None, rc=None, background_task=None):
        self.stdout = stdout
        self.stderr = stderr
        self.rc = rc
        self.background_task = background_task


class cli:
    @staticmethod
    def _run_cmd(cmd):
        debug(f"Executing: {cmd}")
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        (stdout_data, stderr_data) = proc.communicate()
       
        return cli_output(
            stdout=stdout_data.decode().splitlines(),
            stderr=stderr_data.decode().splitlines(),
            rc=proc.returncode,
            background_task=None
        )


class backrestconfig:
    def __init__(self):
        self.path = '/etc/pgbackrest.conf'
        self.config = ConfigParser()
        self.config.read(self.path)

    def flush(self):
        with open(self.path, 'w') as configfile:
            self.config.write(configfile)

    def add_cluster(self, stanza):
        debug(f"Adding Cluster {stanza}")
        try:
            self.config.add_section(stanza)
            self.flush()
        except DuplicateSectionError:
            warning(f"{stanza} allready exists as configsection")
        return True

    def delete_cluster(self, stanza):
        self.config.remove_section(stanza)
        self.flush()

    def add_key(self, stanza, key, value):
        debug(f"Adding Key {stanza} {key} {value}")
        self.config.set(stanza, key, value)
        self.flush()

    def as_dict(self):
        out = {}
        for section in self.config.sections():
            out[section] = {}
            for key in self.config[section]:
                out[section][key] = self.config[section][key]
        return out

    def dict_merge_into(self, target):
        conf_dict = self.as_dict()
        resultdict = {}
        for key in target:
            resultdict[key] = target[key]
        for key in conf_dict:
            if key in resultdict:
                resultdict[key] = {**conf_dict[key], **resultdict[key]}
            else:
                resultdict[key] = conf_dict[key]
        return resultdict


class backrest(cli):

    @staticmethod
    def info():
        out = cli._run_cmd(
            ["pgbackrest", "info", "--output=json"])
        json_out = json.loads(''.join(out.stdout))

        return (json_out, out.stderr)

    @staticmethod
    def stanza_create(stanza):
        out = cli._run_cmd(
            ["pgbackrest", "start", "--stanza", stanza, ])
        out = cli._run_cmd(
            ["pgbackrest", "stanza-create", "--stanza", stanza, ])
        return (''.join(out.stdout), out.stderr, out.rc)

    @staticmethod
    def stanza_delete(stanza):
        out = cli._run_cmd(
            ["pgbackrest", "stop", "--stanza", stanza, '--force'])
        out = cli._run_cmd(
            ["pgbackrest", "stanza-delete", "--stanza", stanza, '--force'])
        return (''.join(out.stdout), out.stderr, out.rc)

    @staticmethod
    def stanza_check(stanza):
        out = cli._run_cmd(
            ["pgbackrest", "check", "--stanza", stanza, '--log-level-console=info'])
        return (out.rc, out.stdout, out.stderr)

    @staticmethod
    def backup(stanza, kind):
        cli._run_cmd(["systemctl", "--user", "restart",
                      f'{stanza}-{kind}-backupjob'])
        state = backrest.check_systemd_servicestate(
            cluster_identifier=stanza, kind=kind)
        pid = state['MainPID']
        ts_start = state['ExecMainStartTimestamp']
        return {'pid': pid, 'ts_start': ts_start}

    @staticmethod
    def list_backups(stanza):
        out = cli._run_cmd(
            ["pgbackrest", "info", "--stanza", stanza, '--log-level-console=info', '--output=json'])
        json_out = json.loads(''.join(out.stdout))
        return (json_out, out.stderr, out.rc)

    @staticmethod
    def backuplog_pid(pid):
        out = cli._run_cmd(
            ['sudo','journalctl',f'_PID={pid}']
        )
        return out

    @staticmethod
    def check_systemd_servicestate(kind, cluster_identifier):
        out = cli._run_cmd(["systemctl", "--user", "--no-page",
                            "show", f'{cluster_identifier}-{kind}-backupjob'])
        service_state = {}
        for line in out.stdout:
            parts = line.split('=')
            service_state[parts[0]] = parts[1]
        return service_state

    @staticmethod
    def check_systemd_bsf(kind, cluster_identifier):
        svc_filename = os.path.join(Path.home(
        ), '.config/systemd/user', f'{cluster_identifier}-{kind}-backupjob.service')
        if os.path.isfile(svc_filename):
            return True
        else:
            return False

    @staticmethod
    def create_systemd_backupservice(kind, cluster_identifier):
        sfc = f'''
[Unit]
Description={cluster_identifier}-{kind}-backupjob

[Service]
Type=simple
ExecStart=/usr/bin/pgbackrest backup --stanza {cluster_identifier} --start-fast --log-level-console=info --type={kind}
RemainAfterExit=false
StandardOutput=journal
RuntimeMaxSec=infinity
        '''
        servicename = f'{cluster_identifier}-{kind}-backupjob.service'
        servicepath = os.path.join(Path.home(), '.config/systemd/user')
        try:
            os.mkdir(servicepath)
        except FileExistsError:
            pass

        with open(os.path.join(servicepath, servicename), 'w') as fout:
            fout.write(sfc)
