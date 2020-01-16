from flask import Flask, jsonify
from flask_restful import Api
from importlib import import_module
from pgapi.helper import Config
import logging

class ServerAPI(object):

    config = None
    server_app = None
    server_api = None
    api_modules = ["clusterAPI", "systemAPI","backupAPI"]

    def __init__(self):
        #__modules = ["clusterAPI"]
        # Config Setup
        self.config = Config.getInstance()

        if self.config.loadConfigFile(self.config.getSetting("config_file")) is not True:
            logging.info("Could not load config file \"%s\". Using Defaults.", self.config.getSetting("config_file"))

        if self.config.getSetting("debug"):
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("debugging enabled")


    def registerHandler(self):
        """Register all modules as well as some special handler."""
        self.server_app.add_url_rule("/", "index", self.index)

        for mod in self.api_modules:
            module = import_module('pgapi.' + mod)
            module.registerHandlers(self.server_api)
        
    def index(self):
        """Print available functions."""
        func_list = {}
        for rule in self.server_app.url_map.iter_rules():
            func_list[rule.rule] = self.server_app.view_functions[rule.endpoint].__doc__
        return jsonify(func_list)

    def setup(self):
        """Setup Flask and FlaskAPI using provided using Config class."""
        appname = self.config.getSetting("name")
        self.server_app = Flask(appname)
        self.server_api = Api(self.server_app)
        self.registerHandler()
        # Needed for wsgi
        return (self.server_app, self.server_api)

    def start(self):
        """Start the server."""
        debug = self.config.getSetting("debug")
        port = self.config.getSetting("port")
        ssl_mode = self.config.getSetting("ssl_mode")
        host = self.config.getSetting("listen_address")
        if ssl_mode == "adhoc":
            ssl = "adhoc"
        else:
            ssl = None
            
        self.server_app.run(debug=debug, host=host, port=port, ssl_context=ssl)

if __name__ == '__main__':
    server = ServerAPI()
    server.setup()
    server.start()
