
from flask import jsonify, abort
from flask_restful import Resource, reqparse
import logging

from pgapi.backrest import backrest as backup
from pgapi.cliclasses import background_task


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
    def get(self,action_uuid=None, min_line=0):
        out={}
        logging.debug( action_uuid )
        for active_task in background_task.active:
            if action_uuid != None and active_task.uuid != action_uuid:
                continue
            logging.debug( active_task.uuid )
            out[active_task.uuid] = {}
            out[active_task.uuid]['stdout']=[]
            out[active_task.uuid]['stderr']=[]
            out[active_task.uuid]['process']=active_task.label
            out[active_task.uuid]['rc']= active_task.rc
            for line in active_task.stdout.get_new_lines(min_line):
                out[active_task.uuid]['stdout'].append(str(line))
            for line in active_task.stderr.get_new_lines(min_line):
                out[active_task.uuid]['stderr'].append( str(line) )
        return jsonify(out)

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
            out = { **out, **({"info":backup().info()}) }
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
            raise NotImplementedError
            # delete a backup            
            # return jsonify( out )
        elif cluster_identifier:
            out = backup().remove_cluster(cluster_identifier)
            return jsonify(out)
            # delete a cluster
            # this is only the case when no backup will be deleted
        # return jsonify(backups)


def registerHandlers(api):
    api.add_resource(_Activity, '/backup_activity/', endpoint="backup_activity")
    api.add_resource(_Activity, '/backup_activity/<string:action_uuid>/', endpoint="backup_activity_uuid")
    api.add_resource(_Activity, '/backup_activity/<string:action_uuid>/<int:min_line>/', endpoint="backup_activity_uuid_min_line")

    api.add_resource(_Backup, '/backup/', endpoint="backup")
    api.add_resource(_Backup, '/backup/<string:cluster_identifier>',
                     endpoint="backup_cluster_identifier")
    api.add_resource(_Backup, '/backup/<string:cluster_identifier>/<string:backup_identifier>',
                     endpoint="backup_cluster_identifier_backup_identifier")
