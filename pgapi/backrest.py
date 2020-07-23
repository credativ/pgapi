from logging import critical, debug, info, log, warning
from re import match

import pgapi.clusterCommands as cc
from flask import abort, jsonify
from flask_restful import reqparse
from pgapi.backupsolution import backupsolution
from pgapi.cliclasses import backrest as backrest_cli
from pgapi.cliclasses import backrestconfig


class backrest(backupsolution):

    def info(self):
        infos = {
            "implementation": "pgBackRest",
            "features": ['incrementalbackups', 'fullbackups', 's3?']
        }
        return infos

    def _list(self):
        (stdout_json, stderr) = backrest_cli.info()
        schema_corrected_output = {}
        for cluster in stdout_json:
            schema_corrected_output[cluster['name']] = {}
            for backup in cluster['backup']:
                schema_corrected_output[cluster['name']
                                        ][backup['label']] = backup

        cnf = backrestconfig().dict_merge_into(schema_corrected_output)
        debug(f"pgbackrest config and backups:\n{cnf}")
        return schema_corrected_output

    def list_backups(self, cluster_identifier=None, backup_identifier=None):
        all_clusters = self._list()
        out = all_clusters
        if cluster_identifier:
            if cluster_identifier in all_clusters:
                out = all_clusters[cluster_identifier]
                if len(out.keys()) == 0:
                    out = {
                        "message": f"No Backups found for cluster {cluster_identifier}"}
            else:
                return abort(500, f"Cluster {cluster_identifier} does not exist")
        elif backup_identifier:
            return abort(500, "Backupdetails not implemented")
        return out

    def backuplog_pid(self,cluster_identifier,pid):
        try:
            if int(pid) > 0:            
                out=backrest_cli.backuplog_pid(pid)                
                if match(f'.*{cluster_identifier}.*',out.stdout[1]):
                    return {'msg': out.stdout}
                else:
                    return {'msg':f'PID {pid} was no backup process for {cluster_identifier}'}
        except ValueError:        
            return {'msg':f'No Backuplog for PID {pid} found'}



    def _take_backup(self, cluster_identifier,kind):
        if not backrest_cli.check_systemd_bsf(kind, cluster_identifier):
            backrest_cli.create_systemd_backupservice(kind, cluster_identifier)
        service_state=backrest_cli.check_systemd_servicestate(cluster_identifier=cluster_identifier,kind=kind)
        if service_state['SubState'] != 'running':
            out = backrest_cli.backup(stanza=cluster_identifier, kind=kind)
            ret = f"{kind}-Backup for {cluster_identifier} started at {out['ts_start']} ({out['pid']})"
        else:
            ret = f"{kind}-Backup for {cluster_identifier} already in progress ({service_state['MainPID']}))"    
        return {'msg': ret}

    def _take_full_backup(self, cluster_identifier=None):
        out = self._take_backup(kind='full', cluster_identifier=cluster_identifier)
        return out

    def _take_incremental_backup(self, cluster_identifier=None):
        out = self._take_backup(kind='incr', cluster_identifier=cluster_identifier)
        return out

    def _check_cluster(self, cluster_identifier):
        (rc, stdout, stderr) = backrest_cli.stanza_check(cluster_identifier)
        if rc == 37:
            # Stanza does not exist
            warning(f"stdout: {stdout}\nstderr: {stderr}")
            return (rc, stdout, stderr)
        elif rc == 87:
            # archive-mode = off
            warning(f"stdout: {stdout}\nstderr: {stderr}")
            return (rc, stdout, stderr)
        elif rc == 0:
            return (rc, stdout, stderr)
        else:
            # other errors
            warning(f"stdout: {stdout}\nstderr: {stderr}")
            return (rc, stdout, stderr)

    def _add_archive_config(self, cluster_identifier, request_args):
        vn = cluster_identifier.split('-')
        version = vn[0]
        name = vn[1]
        (rc, stdout, stderr) = cc.cluster_set_setting(
            version, name, 'archive_mode', 'on')
        if rc == 0:
            (rc, stdout, stderr) = cc.cluster_set_setting(version, name, 'archive_command',
                                                          f'pgbackrest --stanza={cluster_identifier} archive-push %p')
            if rc == 0:                              
                if 'auto_restart' in request_args and request_args['auto_restart'] in ["true", "True"]:
                    (rc, stdout, stderr) = cc.cluster_ctl(
                        version, name, action="restart")
                    return {'rc': rc, "stdout": stdout, "stderr": stderr}
                else:
                    return {'rc': rc, 'stdout': f'You need to restart cluster {cluster_identifier}', 'stderr': stderr}
            else:
                return abort(500, {rc, stdout, stderr})
        else:
            return abort(500, {rc, stdout, stderr})

    def add_cluster(self, cluster_identifier, request_args):
        try:
            data_dir = [instance['config']['data_directory']
                        for instance in cc.cluster_get_all()
                        if instance['config']['cluster_name'] == cluster_identifier.replace('-', '/')][0]
        except LookupError:
            return abort(500, "Cluster does not exist")

        brc = backrestconfig()
        returnmsgs = []
        (status, stdout, stderr) = self._check_cluster(cluster_identifier)
        if status == 37:
            # Stanza does not exist
            debug(f"Datadir is {data_dir}")
            brc.add_cluster(cluster_identifier)
            brc.add_key(cluster_identifier, 'pg1-path', data_dir)

            out = backrest_cli.stanza_create(cluster_identifier)
            returnmsgs.append({"stdout": out[0], "stderr": out[1]})

            out = self._add_archive_config(cluster_identifier, request_args)
            returnmsgs.append(out['stdout'])
        elif status == 87:
            # archive-mode = off
            out = self._add_archive_config(cluster_identifier, request_args)
            returnmsgs.append(out['stdout'])
        elif status == 0:
            returnmsgs.append('Cluster already added')
        else:
            returnmsgs.append({'stdout': stdout, 'stderr': stderr})

        return {'msg': ' / '.join(returnmsgs)}

    def remove_cluster(self, cluster_identifier=None):
        out = backrest_cli.stanza_delete(cluster_identifier)
        brc = backrestconfig()
        brc.delete_cluster(cluster_identifier)

        return {"stdout": out[0], "stderr": out[1]}

    def check(self, cluster_identifier=None,):
        pass
