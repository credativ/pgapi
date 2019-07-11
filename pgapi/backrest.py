from pgapi.backupsolution import backupsolution
from pgapi.cliclasses import backrest as backrest_cli, backrestconfig
from logging import debug, log, info, warning, critical

from pgapi.clusterCommands import cluster_get_all

from flask_restful import reqparse


class backrest(backupsolution):

    def info(self):
        infos={"implementation":"pgBackRest",
            "features":['incrementalbackups','fullbackups','s3?']}
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
        print(cnf)
        return schema_corrected_output

    def list_backups(self, cluster_identifier=None, backup_identifier=None):
        all_clusters = self._list()
        out = all_clusters
        if cluster_identifier:
            if cluster_identifier in all_clusters:
                out = all_clusters[cluster_identifier]
            else:
                raise Exception("Cluster does not exist")
        elif backup_identifier:
            raise Exception("Backupdetails not yet implemented")

        return out

    def _take_full_backup(self, cluster_identifier=None, ):
        out = backrest_cli.backup(cluster_identifier )
        return {"stdout": out[0], "stderr": out[1]}

    def add_cluster(self, cluster_identifier=None):
        parser = reqparse.RequestParser()
        parser.add_argument("pg1-path", type=str, default=None)
        args = parser.parse_args(strict=False)

        brc = backrestconfig()
        brc.add_cluster(cluster_identifier)

        
        #brc.add_key(cluster_identifier, 'pg1-path', args['pg1-path'])
        try:
            data_dir = [instance['config']['data_directory']
                        for instance in cluster_get_all() 
                            if instance['config']['cluster_name'] == cluster_identifier.replace('-','/') ][0]
        except LookupError as e:
            raise Exception("Cluster does not exist.")
        debug(f"Datadir is {data_dir}")
        #[0]['config']['data_directory']
        brc.add_key(cluster_identifier, 'pg1-path', data_dir)

        out = backrest_cli.stanza_create(cluster_identifier )
        return {"stdout": out[0], "stderr": out[1]}

    def remove_cluster(self, cluster_identifier=None):
        out = backrest_cli.stanza_delete(cluster_identifier)
        brc = backrestconfig()
        brc.delete_cluster(cluster_identifier)

        return {"stdout": out[0], "stderr": out[1]}

    def check(self, cluster_identifier=None,):
        pass
