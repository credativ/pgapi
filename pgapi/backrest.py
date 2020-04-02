from pgapi.backupsolution import backupsolution
from pgapi.cliclasses import backrest as backrest_cli, backrestconfig
from logging import debug, log, info, warning, critical

from pgapi.clusterCommands import cluster_get_all
import pgapi.clusterCommands as cc

from flask_restful import reqparse
from flask import jsonify, abort


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

    def _take_backup(self, kind, cluster_identifier=None):
        out = backrest_cli.backup(cluster_identifier, kind)
        return out

    def _take_full_backup(self, cluster_identifier=None):
        out = self._take_backup('full',cluster_identifier)
        return {"stdout": out.stdout, "stderr": out.stderr}

    def _take_incremental_backup(self, cluster_identifier=None):
        out = self._take_backup('incr',cluster_identifier)
        return {"stdout": out.stdout, "stderr": out.stderr}

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

    def _add_archive_config(self, cluster_identifier):
        vn = cluster_identifier.split('-')
        version = vn[0]
        name = vn[1]
        (rc, stdout, stderr) = cc.cluster_set_setting(
            version, name, 'archive_mode', 'on')
        warning(f"archive_mode on rc = {rc}")
        if rc == 0:
            (rc, stdout, stderr) = cc.cluster_set_setting(version, name, 'archive_command',
                                                          f'pgbackrest --stanza={cluster_identifier} archive-push %p')
            warning(f"archive_command rc = {rc}")
            if rc == 0:
                return {'rc': 0, 'stdout': f'You need to restart cluster {cluster_identifier}', 'stderr': ''}
            else:
                return abort(500, {rc, stdout, stderr})
        else:
            return abort(500, {rc, stdout, stderr})

        # In case we want to restart the cluster automatically later
        # (returncode, stdout, stderr) = cc.cluster_ctl(version, name, action="restart")
        # log(f"out: {stdout} \nerr: {stderr}\n rc:{returncode}")

    def add_cluster(self, cluster_identifier=None):
        try:
            data_dir = [instance['config']['data_directory']
                        for instance in cluster_get_all()
                        if instance['config']['cluster_name'] == cluster_identifier.replace('-', '/')][0]
        except LookupError:
            return abort(500, "Cluster does not exist")

        brc = backrestconfig()
        returnmsgs = []
        (status,stdout, stderr) = self._check_cluster(cluster_identifier)
        if status == 37:
            # Stanza does not exist
            debug(f"Datadir is {data_dir}")
            brc.add_cluster(cluster_identifier)
            brc.add_key(cluster_identifier, 'pg1-path', data_dir)

            out = backrest_cli.stanza_create(cluster_identifier)
            returnmsgs.append({"stdout": out[0], "stderr": out[1]})

            out = self._add_archive_config(cluster_identifier)            
            returnmsgs.append(out['stdout'])
        elif status == 87:
            # archive-mode = off
            out = self._add_archive_config(cluster_identifier)
            returnmsgs.append(out['stdout'])
        elif status == 0:
            returnmsgs.append('Cluster already added')
        else:
            returnmsgs.append({'stdout': stdout, 'stderr': stderr})

        return returnmsgs
    def remove_cluster(self, cluster_identifier=None):
        out = backrest_cli.stanza_delete(cluster_identifier)
        brc = backrestconfig()
        brc.delete_cluster(cluster_identifier)

        return {"stdout": out[0], "stderr": out[1]}

    def check(self, cluster_identifier=None,):
        pass
