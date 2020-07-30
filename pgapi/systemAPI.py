from flask import jsonify, abort
from flask_restful import Resource, reqparse
import logging

from pgapi.systemCommands import *
from pgapi import tmate

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

class Tmate(Resource):

    def get(self):
        ini=tmate.otmate()        
        logging.info("GET Request for Tmate-Instanzes")
        return jsonify(ini.get_tmate())
    
    def put(self):
        ini=tmate.otmate()
        logging.info("PUT Request to start a new tmate-session")
        ini.start_tmate()
        return jsonify(ini.get_tmate())

def registerHandlers(api):
    api.add_resource(System, '/system/', endpoint="system")
    api.add_resource(System, '/system/<string:section>/', endpoint="system_section")
    api.add_resource(Tmate, '/tmate/', endpoint="tmate")
