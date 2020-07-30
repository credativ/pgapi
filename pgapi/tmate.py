from glob import glob
import subprocess
import os
from pathlib import Path
import logging

from pgapi import helper
from pgapi import cliclasses


class otmate:

    def __init__(self):
        self.config = helper.Config()
        self.cli=cliclasses.cli

    def create_tmate_service(self):
        tconf = self.config.getSetting('tmate_config')
        if os.path.isfile(tconf):
            toptions = '-f {}'.format(tconf)
        else:
            toptions=''

        sfc = f'''
[Unit]
Description=tmate

[Service]
Type=forking
ExecStart=/usr/bin/tmate {toptions} new-session -s pgapi -d
StandardOutput=journal
RuntimeMaxSec=infinity
            '''
        servicename = 'tmate.service'
        servicepath = os.path.join(Path.home(), '.config/systemd/user')
        try:
            os.mkdir(servicepath)
        except FileExistsError:
            pass

        with open(os.path.join(servicepath, servicename), 'w') as fout:
            fout.write(sfc)

    def check_systemd_servicestate(self):
        out = self.cli._run_cmd(["systemctl", "--user", "--no-page",
                            "show", 'tmate'])
        service_state = {}
        for line in out.stdout:
            parts = line.split('=')
            service_state[parts[0]] = parts[1]
        return service_state


    def check_systemd_bsf(self):
        svc_filename = os.path.join(Path.home(
        ), '.config/systemd/user', 'tmate.service')
        if os.path.isfile(svc_filename):
            return True
        else:
            return False

    def execute_tmate(self):
        self.cli._run_cmd(["systemctl", "--user", "start",
                      'tmate'])
        state = self.check_systemd_servicestate()
        pid = state['MainPID']
        ts_start = state['ExecMainStartTimestamp']
        return {'pid': pid, 'ts_start': ts_start}


    def start_tmate(self):
        """
        tmate -f ~/tmate.conf
        tmate -S /tmp/tmate-0/mMnCU6 show-messages
        """
        self.create_tmate_service()

        service_state=self.check_systemd_servicestate()
        if service_state['SubState'] != 'running':
            out=self.execute_tmate()
            ret = f"tmate started at {out['ts_start']} ({out['pid']})"
        else:
            state = self.check_systemd_servicestate()
            pid = state['MainPID']
            ts_start = state['ExecMainStartTimestamp']
            sessioninfo=self.get_tmate()
            ret = f"tmate already started at {ts_start} (PID {pid}).\n{sessioninfo}"    
        return {'msg': ret}        

    def get_tmate(self):
        uid=os.getuid()
        try:
            tsocket = glob(f'/tmp/tmate-{uid}/*')[0]
            session_call=['tmate','-S ',tsocket,'show-messages']
            sessioninfo=cliclasses.cli._run_cmd(session_call)
        except IndexError:
            sessioninfo="No active tmate-session found"
        logging.info(sessioninfo)
        return sessioninfo