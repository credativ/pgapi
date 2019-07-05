from subprocess import Popen, PIPE
from logging import warning, debug

from threading import Thread
from collections import deque
import json

from configparser import ConfigParser, DuplicateSectionError

background_tasks = []

class logline:
    def __init__(self, line_nr, content):
        self.line_nr=line_nr
        self.content=content
    def __str__(self):
        return (f"{self.line_nr} - {self.content}")

    def __gt__(self, comparator):
        if not comparator:
            return True;
        return self.line_nr > comparator.line_nr

class read_channel(Thread):
    def __init__(self, channel):
        Thread.__init__(self)
        self.channel = channel
        self.content = deque(maxlen=30)
        self.last_returned = None
    def get_new_lines(self, line_nr=None):
        comparator = line_nr if line_nr else self.last_returned
        for line in self.content:
            if not line_nr:
                self.last_returned = line
            if line > comparator:
                yield line 
    def run(self):
        debug("Starting to poll channel ")
        for line_nr, line in enumerate(self.channel):
            self.content.append( logline(line_nr, line)  )
        debug("Finished polling channel ")

class background_task(Thread):
    def __init__(self, proc):
        Thread.__init__(self)
        self.proc = proc
        background_tasks.append(self)

    def run(self):
        debug("Starting async task")
        self.proc.poll()
        stderr = read_channel( self.proc.stderr)
        stdout = read_channel( self.proc.stdout)
        stderr.start()
        stdout.start()
        import time
        while True:
            self.proc.poll()
            for line in stderr.get_new_lines():
                debug(f"STDERR: {line}")
            for line in stdout.get_new_lines():
                debug(f"STDERR: {line}")
            if self.proc.returncode != None:
                debug("Job Finished")
                stderr.join()
                stdout.join()
                break
            time.sleep(1)


class cli:
    @staticmethod
    def _run_cmd(cmd, blocking=True):
        global background_tasks
        debug("Executing: %s with Blocking=%s" % (str(cmd), blocking))
        proc = Popen(['sudo','-u','postgres']+cmd, stdout=PIPE, stderr=PIPE)

        background_tasks = [process for process in background_tasks if not process.isAlive() ]
        

        if blocking == False:
            if len(background_tasks) > 1:
                warning("More than 1 job active")
            background_task(proc).start()
            return ("Task Started...", "", "0" )
        else:
            proc.poll()
            return ([line.strip().decode('ascii') for line in proc.stdout], [line.strip().decode() for line in proc.stderr], proc.returncode)


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
        (stdout, stderr, _) = cli._run_cmd(
            ["pgbackrest", "info", "--output=json"],  blocking=True)
        json_out = json.loads(''.join(stdout))

        return (json_out, stderr)
    @staticmethod
    def stanza_create(stanza):
        (stdout, stderr, rc) = cli._run_cmd(
            ["pgbackrest", "start", "--stanza", stanza, ],  blocking=True)
        (stdout, stderr, rc) = cli._run_cmd(
            ["pgbackrest", "stanza-create", "--stanza", stanza, ],  blocking=True)
        return (''.join(stdout), stderr, rc)

    @staticmethod
    def stanza_delete(stanza):
        (stdout, stderr, rc) = cli._run_cmd(
            ["pgbackrest", "stop", "--stanza", stanza, '--force'],  blocking=True)
        (stdout, stderr, rc) = cli._run_cmd(
            ["pgbackrest", "stanza-delete", "--stanza", stanza, '--force'],  blocking=True)
        return (''.join(stdout), stderr, rc)

    @staticmethod
    def backup(stanza):
        (stdout, stderr, rc) = cli._run_cmd(
            ["pgbackrest", "backup", "--stanza", stanza, "--start-fast"],  blocking=False)
        return (''.join(stdout), stderr, rc)
