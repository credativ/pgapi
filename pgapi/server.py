from flask import Flask, jsonify
from flask_restful import Api
from importlib import import_module
from pgapi.helper import Config

class ServerAPI(object):

    _config = None
    server_app = None
    server_api = None

    __api_modules = ["clusterAPI", "systemAPI","backupAPI"]
    #__modules = ["clusterAPI"]

    def registerHandler(self):
        """Register all modules as well as some special handler."""
        self.server_app.add_url_rule("/", "index", self.index)

        for mod in self.__api_modules:
            module = import_module('pgapi.' + mod)
            module.registerHandlers(self.server_api)
        
    def index(self):
        """Print available functions."""
        func_list = {}
        for rule in self.server_app.url_map.iter_rules():
            func_list[rule.rule] = self.server_app.view_functions[rule.endpoint].__doc__
        return jsonify(func_list)

    def setup(self, config):
        """Setup Flask and FlaskAPI using provided using Config class."""
        self._config = config
        appname = self._config.getSetting("name")
        self.server_app = Flask(appname)
        self.server_api = Api(self.server_app)

        self.registerHandler()
        return (self.server_app, self.server_api)

    def start(self):
        """Start the server."""
        debug = self._config.getSetting("debug")
        port = self._config.getSetting("port")
        ssl_mode = self._config.getSetting("ssl_mode")
        host = self._config.getSetting("listen_address")
        if ssl_mode == "adhoc":
            ssl = "adhoc"
        else:
            ssl = None
            
        self.server_app.run(debug=debug, host=host, port=port, ssl_context=ssl)
