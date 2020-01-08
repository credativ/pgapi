from flask import jsonify, abort
from flask_restful import Resource, reqparse
import logging
from pgapi.clusterCommands import *

class Cluster(Resource):
    _states = ["start", "stop", "restart", "reload", "promote", "status"]
    
    def _findCluster(self, version, name):
        """Helper function to exctract the first cluster from a
           list of all matching clusters.
        """
        clusters = cluster_get(version, name)
        if len(clusters) <= 0:
            err_message = "The requested Cluster (version='{}', name='{}' does not exist"
            err_message = err_message.format(version, name)
            abort(404, err_message)

        return clusters[0]

    def _clusterExists(self, version, name):
        if len(cluster_get(version, name)) >= 1:
            return True

        return False

    def _abortIfClusterDoesNotExists(self, version, name):
        if not self._clusterExists(version, name):
            err_message = "The requested Cluster (version='{}', name='{}' does not exists"
            err_message = err_message.format(version, name)
            abort(404, err_message)
            
    def _abortIfClusterExists(self, version, name):
        if self._clusterExists(version, name):
            err_message = "The requested Cluster (version='{}', name='{}' already exists"
            err_message = err_message.format(version, name)
            abort(409, err_message)

    def get(self, version, name):
        """Return a cluster identified by version and name.

           Example: GET /cluster/9.6/main
        """
        logging.info("GET Request for Cluster \"%s-%s\"", version, name)

        return jsonify(self._findCluster(version, name))

    def post(self, version, name):
        """Create a new cluster identified by version and name
           and return it.

           Example: POST /cluster/9.6/main
        """
        self._abortIfClusterExists(version, name)

        parser = reqparse.RequestParser()
        parser.add_argument("port", type=int, default=None)
        parser.add_argument("data-checksums", type=bool, default=None)
        parser.add_argument("primary_conninfo", type=str, default=None)


        args = parser.parse_args(strict=True)

        (rc, out, err) = cluster_create(version, name, args)
        if 0 != rc:
            return {"returncode": rc, "stdout": out, "stderr": err}, 500

        return self._findCluster(version, name), 201

    def delete(self, version, name):
        """Delete a cluster identified by version and name.

           Example: DELETE /cluster/9.6/main
        """
        self._abortIfClusterDoesNotExists(version, name)

        (rc, out, err) = cluster_drop(version, name)
        if 0 != rc:
            return {"returncode": rc, "stdout": out, "stderr": err}, 500

        return "Success", 200

    def patch(self, version, name):
        """Update a cluster State.
           Update only attributes that are provided by the client request.
           All other attributes are not modified by PATCH requests.

           Valid payload:
              config(dict)  -- any postgresql setting an value
                               Example: "port": 5490
              state(string) -- Target state of the cluster instance (see _states)

           Example: curl -i -X PATCH \
                         -H "Content-Type: application/json" \
                         -d '{"config": {"port": 5490}, "state": "start"}' \
                         http://127.0.0.1:15432/cluster/9.6/asdf
        """
        self._abortIfClusterDoesNotExists(version, name)

        # For now we only accept "config" and "state" other attributes
        # will be added in the future.
        parser = reqparse.RequestParser()
        parser.add_argument("config", type=dict, default={})
        parser.add_argument("state", type=str, default=None)

        # Update each value found in config
        args = parser.parse_args(strict=True)
        logging.info(args["config"])
        for setting, value in args["config"].items():
            logging.info("Set \"%s\" to \"%s\"", setting, value)
            (rc, out, err) = cluster_set_setting(version, name, setting, value)
            if rc != 0:
                return {"rc": rc, "stdout": out, "stderr": err}, 500

        # Update the cluster state
        if args["state"] is not None:
            logging.info("state \"%s\" requested", args["state"])
            if not args["state"] in self._states:
                err_message = "Requested state not valid. Valid states are {}."
                err_message = err_message.format(",".join(self._states))
                abort(400, err_message)

            # Check if the cluster is already in wanted state.
            # We do this check only for start, stop and promote.
            cluster = self._findCluster(version, name)
            running = cluster["running"]
            if "recovery" in cluster:
                recovery = cluster["recovery"]
            else:
                recovery = 0

            if (running == 0 and args["state"] == "stop") or \
               (running == 1 and args["state"] == "start") or \
               (recovery == 0 and args["state"] == "promote"):
                return self._findCluster(version, name), 200

            (rc, out, err) = cluster_ctl(version, name, args["state"]) 
            if rc != 0:
                return {"rc": rc, "stdout": out, "stderr": err}, 500

        return self._findCluster(version, name), 200
        

class ClusterList(Resource):
   def get(self):
       """Returns a list of all clusters found on the system.
          
          Example: GET /cluster/
       """
       return jsonify(cluster_get_all())

def registerHandlers(api):
    api.add_resource(Cluster, '/cluster/<string:version>/<string:name>')
    api.add_resource(ClusterList, '/cluster/')
