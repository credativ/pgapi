from subprocess import Popen, PIPE
from logging import warning, debug

from threading import Thread
from collections import deque
import json
import uuid
import time
import datetime

from configparser import ConfigParser, DuplicateSectionError

background_tasks = []


class logline:
    def __init__(self, line_nr, content):
        self.line_nr = line_nr
        self.content = content

    def __str__(self):
        return (f"{self.line_nr} - {self.content}")

    def __gt__(self, comparator):
        if not comparator:
            return True
        return int(self) > int(comparator)

    def __int__(self):
        return self.mkdiline_nr


class read_channel(Thread):
    def __init__(self, channel):
        Thread.__init__(self)
        self.channel = channel
        self.content = deque(maxlen=100)
        self.last_returned = None

    def get_new_lines(self, line_nr=None):
        comparator = line_nr if line_nr != None else self.last_returned

        for line in self.content:
            if not line_nr:
                self.last_returned = line
            if line > comparator:
                yield line

    def run(self):
        debug("Starting to poll channel ")
        for line_nr, line in enumerate(self.channel):
            self.content.append(logline(line_nr, line))
        debug("Finished polling channel ")


class background_task(Thread):
    active = []

    def __init__(self, proc, label='Unnamed'):
        Thread.__init__(self)
        self.proc = proc
        self.uuid = str(uuid.uuid4())  # No need to keep the uuid-class around,
                                       # also it will break jsonify
                                       
        self.stderr = None
        self.label = label
        self.stdout = None
        self.rc = None
        self.finished = None
        background_task.active.append(self)

    def run(self):
        debug("Starting async task")
        self.proc.poll()
        self.stderr = read_channel(self.proc.stderr)
        self.stdout = read_channel(self.proc.stdout)

        self.stderr.start()
        self.stdout.start()
        while True:
            self.proc.poll()
            if self.proc.returncode != None:
                self.rc = self.proc.returncode
                debug("Job Finished")
                break
            time.sleep(1)
        self.finished = datetime.datetime.now()

    def reached_ttl(self):
        if self.finished == None:
            return False
        return self.finished + datetime.timedelta(minutes=5) > datetime.datetime.now()


class cli_output():
    def __init__(self, stdout=None, stderr=None, rc=None, background_task=None):
        self.stdout = stdout
        self.stderr = stderr
        self.rc = rc
        self.background_task = background_task


class cli:
    @staticmethod
    def _run_cmd(cmd, blocking=True):
        global background_tasks
        debug("Executing: %s with Blocking=%s" % (str(cmd), blocking))
        proc = Popen(['sudo', '-u', 'postgres']+cmd, stdout=PIPE, stderr=PIPE)

        background_task.active = [
            process for process in background_task.active if not process.isAlive() and process.reached_ttl()]

        if blocking == False:
            if len(background_task.active) > 100:
                warning("More than 100 jobs in memory")
            active_background_task = background_task(proc, ' '.join( cmd ) )
            active_background_task.start()
            return cli_output(
                stdout='Async task startet',
                stderr="",
                rc=None,
                background_task=active_background_task
            )
        else:
            proc.poll()
            return cli_output(
                stdout=[line.strip().decode('ascii') for line in proc.stdout],
                stderr=[line.strip().decode() for line in proc.stderr],
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

            ["pgbackrest", "info", "--output=json"],  blocking=True)
        json_out = json.loads(''.join(out.stdout))

        return (json_out, out.stderr)

    @staticmethod
    def stanza_create(stanza):
        out = cli._run_cmd(
            ["pgbackrest", "start", "--stanza", stanza, ],  blocking=True)
        out = cli._run_cmd(
            ["pgbackrest", "stanza-create", "--stanza", stanza, ],  blocking=True)
        return (''.join(out.stdout), out.stderr, out.rc)

    @staticmethod
    def stanza_delete(stanza):
        out = cli._run_cmd(
            ["pgbackrest", "stop", "--stanza", stanza, '--force'],  blocking=True)
        out = cli._run_cmd(
            ["pgbackrest", "stanza-delete", "--stanza", stanza, '--force'],  blocking=True)
        return (''.join(out.stdout), out.stderr, out.rc)

    @staticmethod
    def backup(stanza):
        out = cli._run_cmd(
            ["pgbackrest", "backup", "--stanza", stanza, "--start-fast", '--log-level-console=info'],  blocking=False)
        return (''.join(out.stdout), out.stderr, out.rc)
