from flask import jsonify, abort
from flask_restful import Resource, reqparse
import logging

from pgapi.serverCommands import *

class System(Resource):

    def get(self, section=None):
        """Return global system informations.

           Example: GET /system
        """
        logging.info("GET Request for System information, section=\"%s\"", section)

        system_info = get_system_info(section)

        return jsonify(system_info)

def registerHandlers(api):
    api.add_resource(System, '/system/', endpoint="system")
    api.add_resource(System, '/system/<string:section>/', endpoint="system_section")
