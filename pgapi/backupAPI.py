
from flask import jsonify, abort, request
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


class _Activity(Resource):
    def get(self, action_uuid=None, min_line=0):
        out = {'msg':'Not implemented yet'}
        return jsonify(out)

class _Backup(Resource):
    def get(self, cluster_identifier=None, action=None):
        try:
            logging.info("GET Request for Backups")
            out = None
            if cluster_identifier:
                if 'pid' in request.args:                    
                    out = backup().backuplog_pid(cluster_identifier=cluster_identifier,pid=request.args['pid'])
                else:
                    out = backup().list_backups(cluster_identifier=cluster_identifier)
            else:
                out = backup().list_backups()
            #out = { **out, **({"info":backup().info()}) }
            return jsonify(out)
        except Exception as e:
            return abort(500, str(e))

    def put(self, cluster_identifier=None,action=None):
        """PUT creates a cluster or starts a backup"""

        out = None
        # cluster_identifier='11-main'
        if action == 'prepare':        
            out = backup().add_cluster(cluster_identifier=cluster_identifier,request_args=request.args)
        elif action == 'full':
            out = backup().take_backup(kind='full',cluster_identifier=cluster_identifier)
        elif action == 'incremental':
            out = backup().take_backup(kind='incremental',cluster_identifier=cluster_identifier)
        else:
            out={"msg":"supported actions: prepare, full, incremental"}
        return jsonify(str(out))

    def delete(self, cluster_identifier=None, backup_identifier=None):
        logging.info("DELETE Request for Backups")
        if backup_identifier:
            raise NotImplementedError
            # delete a backup
            # return jsonify( out )
        elif cluster_identifier:
            out = backup().remove_cluster(cluster_identifier)
            return jsonify(out)
            # delete a cluster
            # this is only the case when no backup will be deleted
        # return jsonify(backups)



# backup_identifier=$Timestamp

def registerHandlers(api):
    api.add_resource(_Activity, '/backup_activity/',
                     endpoint="backup_activity")
    api.add_resource(_Activity, '/backup_activity/<string:action_uuid>/',
                     endpoint="backup_activity_uuid")
    api.add_resource(_Activity, '/backup_activity/<string:action_uuid>/<int:min_line>/',
                     endpoint="backup_activity_uuid_min_line")

    api.add_resource(_Backup, '/backup/', endpoint="backup")
    api.add_resource(_Backup, '/backup/<string:cluster_identifier>',
                     endpoint="backup_cluster_identifier")
    api.add_resource(_Backup, '/backup/<string:cluster_identifier>/<string:action>',
                     endpoint="backup_cluster_identifier_action")

    # api.add_resource(_Backup, '/backup/<string:cluster_identifier>',
    # endpoint="backup_cluster_identifier_backup_kind")
