from flask import jsonify, abort
from flask_restful import Resource, reqparse
import logging

from pgapi.systemCommands import *

class System(Resource):

    def get(self, section=None):
        """Return global system information.

           Example: GET /system

           It's possible to specify what specific setion to be
           returned by the module. E.g. cpu_config.

           Example: GET /system/cpu_config
        """
        logging.info("GET Request for System information, section=\"%s\"", section)

        system_info = get_system_info(section)

        return jsonify(system_info)

def registerHandlers(api):
    api.add_resource(System, '/system/', endpoint="system")
    api.add_resource(System, '/system/<string:section>/', endpoint="system_section")
