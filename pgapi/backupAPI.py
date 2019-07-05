
from flask import jsonify, abort
from flask_restful import Resource, reqparse
import logging

from pgapi.backrest import backrest as backup
"""
    Backupimplementations share a common API, which makes them plugable via their
    parent 'backup'.

    For the moment, it is not decided when and where the decision for the actual
    implementation is done.

    For the time beeing, this is hardcoded to backrest due to it's use in elephant-shed
    and the lack of alternatives.

    As it is propably done with a configdriven factory, using a rewired backup directly
    should do no harm.
    """


class _Backup(Resource):
    def get(self, cluster_identifier=None, backup_identifier=None):
        try:
            logging.info("GET Request for Backups")
            out = None
            if backup_identifier:
                out = backup().list_backups(backup_identifier=backup_identifier)
            if cluster_identifier:
                out = backup().list_backups(cluster_identifier=cluster_identifier)
            else:
                out = backup().list_backups()
            return jsonify(out)
        except Exception as e:
            return abort(500, str(e))

    def put(self, cluster_identifier=None, backup_identifier=None):
        """PUT creates a cluster or starts a backup.
        To be somewhat REST compliant, it is of no relevance what
        exactly we PUT to as /backupidentifier."""
        out = None
        if (cluster_identifier and not backup_identifier):
            out = backup().add_cluster(cluster_identifier, )
        elif (backup_identifier):
            parser = reqparse.RequestParser()
            parser.add_argument("kind", type=str, default='full')
            args = parser.parse_args(strict=False)
            out = backup().take_backup(cluster_identifier=cluster_identifier, kind=args['kind'])
        return jsonify(str(out))

    def delete(self, cluster_identifier=None, backup_identifier=None):
        logging.info("DELETE Request for Backups")
        if backup_identifier:
            pass
            raise NotImplementedError
            # delete a backup
            #out = backup().remove_cluster( cluster_identifier )
            # return jsonify( out )
        elif cluster_identifier:
            out = backup().remove_cluster(cluster_identifier)
            return jsonify(out)
            # delete a cluster
            # this is only the case when no backup will be deleted
        # return jsonify(backups)


def registerHandlers(api):
    api.add_resource(_Backup, '/backup/', endpoint="backup")
    api.add_resource(_Backup, '/backup/<string:cluster_identifier>',
                     endpoint="backup_cluster_identifier")
    api.add_resource(_Backup, '/backup/<string:cluster_identifier>/<string:backup_identifier>',
                     endpoint="backup_cluster_identifier_backup_identifier")
