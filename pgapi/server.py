from flask import Flask, jsonify
from flask_cors import CORS
from importlib import import_module
from pgapi.helper import Config
from flask_restful_swagger_2 import Api

class ServerAPI(object):

    _config = None
    server_app = None
    server_api = None

    def registerHandler(self):
        """Register all modules as well as some special handler."""
        self.server_app.add_url_rule("/", "index", self.index)
        self.server_app.add_url_rule("/api/doc", "doc", self.doc)
        
        for mod in ["clusterAPI"]:
            module = import_module('pgapi.clusterAPI')
            module.registerHandlers(self.server_api)
    
    def index(self):
        """Print available functions."""
        func_list = {}
        for rule in self.server_app.url_map.iter_rules():
            func_list[rule.rule] = self.server_app.view_functions[rule.endpoint].__doc__
        return jsonify(func_list)

    def doc(self):
        """API Documentation with Swagger"""
        
        return """<head>
        <meta http-equiv="refresh" content="0; url=http://petstore.swagger.io/?url=http://127.0.0.1:15432/api/swagger.json" />
        </head>"""
    
    def setup(self, config):
        """Setup Flask and FlaskAPI using provided using Config class."""
        self._config = config
        appname = self._config.getSetting("name")
        self.server_app = Flask(appname)
        CORS(self.server_app)
        
        #set API and metadata description for the API Documentation
        self.server_api = Api(self.server_app, api_version = '0.0.1',
                              title = 'PGAGPI - REST API for PostgreSQL clusters',
                              terms = '',
                              description = 'pgapi tries to be a simple but useful REST API for Debian based PostgreSQL Systems. It offers a way to create, delete and control PostgreSQL clusters via HTTP requests. '
                                            '</br></br>WARNING: using the "Execute" Buttons will cause real requests and affect your system.',
                              contact = {'name': 'Adrian Vondendriesch', 'url': 'https://github.com/credativ/pgapi/',
                                         'email': 'adrian.vondendriesch@credativ.de'},
                              license = {'name': 'MIT license', 'url': 'https://opensource.org/licenses/MIT'})

        self.registerHandler()
        return (self.server_app, self.server_api)

    def start(self):
        """Start the server."""
        debug = self._config.getSetting("debug")
        port = self._config.getSetting("port")
        ssl_mode = self._config.getSetting("ssl_mode")
        if ssl_mode == "adhoc":
            ssl = "adhoc"
        else:
            ssl = None
            
        print("pgapi listening on: http://127.0.0.1:15432 ...")
        self.server_app.run(debug=True, port=port, ssl_context=ssl)
