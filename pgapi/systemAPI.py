from flask import jsonify, abort
from flask_restful import Resource, reqparse
import logging
from pgapi.serverCommands import *

class System(Resource):

    def get(self):
        """Return global system informations.

           Example: GET /system
        """
        logging.info("GET Request for System information")

        system_info = get_system_info()

        return jsonify(system_info)

def registerHandlers(api):
    api.add_resource(System, '/system/')
