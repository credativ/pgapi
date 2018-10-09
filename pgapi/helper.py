import logging
import os
import yaml
import re

class Config(object): 
    __config = {
        "defaults": {
            "name": "PGAPI",
            "port": 15432,
            "listen_address": "127.0.0.1",
            "debug": False,
            "sudo_user": "postgres",
            "use_sudo": False,
            "config_file": "/etc/pgapi/pgapi.conf",
            "ssl_mode": "off", # off or adhoc
            "bypass_systemd": True,
            "encoding": 'UTF-8'
        },
        "file": {},
        "arguments": {}
    }

    __namespaces = ["arguments", "file", "defaults"]

    __instance = None

    @classmethod
    def getInstance(cls):
        """Get a Config object instance.

        If not already created, it will create a new Config object.
        
        Returns (Config):
           config -- Config object
        """
        if not cls.__instance:
            cls.__instance = Config()
        return cls.__instance
        
    def getSettingAndNamespace(self, setting):
        """Returns the value for a given setting and provides the
        namespace it comes from.

        Function Arguments:
           setting (string) -- setting for which the value will be returned
        
        Returns: tuple (value, namespace)
           value (any)        -- value for setting, if setting is found in any namespace
                              -- None otherwise
           namespace (string) -- namespace, if setting is found in any namespace
                              -- None otherwise
        """
        logging.debug("search for setting: \"%s\"", setting)
        for namespace in self.__namespaces:
            if setting in self.__config[namespace]:
                return (self.__config[namespace][setting], namespace)
        return (None, None)

    def getSetting(self, setting):
        """Returns the value for a given setting.
        """
        (value, _) = self.getSettingAndNamespace(setting)
        return value

    def setSetting(self, namespace, setting, value):
        """Update a setting for a give namespace.
        Valid namespaces are "defaults", "file" and "arguments"

        Function Arguments:
            namespace (string) -- namespace for setting
            setting (string)   -- setting to set
            value (any)        -- value to save

        Returns (bool):
            True -- always

        Throws:
            KeyError -- if namespace is invalid
        """
        logging.debug("update \"%s\" to \"%s\" (namespace: \"%s\")", setting, value, namespace)
        if not namespace in self.__namespaces:
            raise KeyError("\"%s\" is not a valid namespace", namespace)

        self.__config[namespace][setting] = value

        return True

    def loadConfigFile(self, filename):
        """Load a given yaml config into "file" namespace.

        Returns (bool):
            True  -- if the file could be loaded and
            False -- if the file could not be loaded."""
        try:
            with open(filename, 'r') as f:
                self.__config["file"] = yaml.load(f)
        except:
            return False

        return True

def check_regex(pattern, value):
    """Checks a given value against a given regex pattern.

    Function Argmuents:
       pattern (string) -- regex pattern
       value (string)   -- value to compair against the pattern
    
    Returns (bool):
       True  -- if the value matches the provided pattern
       False -- otherwise
    """
    found = re.search(pattern, value)
    if not found:
        return False

    return True
    
def command_is_safe(command):
    """
    Checks if a command is "safe" in the manner of this api.

    We only allow the following characters:
       - [a-z][A-Z]
       - " ", TAB, etc.
       - [0-9]
       - "."
       - "="
       - "-"
       - "/"
    
    Function Arguments:
       command (string) -- command to execute

    Returns (bool):
       True  -- if it's save to execute (regarding the defined regex)
       False -- otherwise
    """
    pattern = r"^[\d\w\s\/\.\-=/]*$"
    return check_regex(pattern, command)

def param_is_safe(param):
    """
    Checks if a postgresql parameter is "safe".
      We only allow the following characters:
      * [a-z][A-Z]
      * "_"

    Function Arguments:
       param (string) -- parameter to check

    Returns (bool):
       True  -- if param seems to be valid (regarding the defined regex)
       False -- otherwise
    """
    pattern = r"^[\w_]*.*[a-zA-Z]+[\w]*$"
    return check_regex(pattern, param)

def valid_cluster_name(name):
    """Checks if a cluster name is valid.
    
    Function Arguments:
       name (string) -- name of the cluster
    
    Returns (bool):
       True  -- if the cluster name is valid (regarding the defined regex)
       False -- otherwise
    """
    pattern = r"^[a-zA-Z]+[\w\-_]*$"
    return check_regex(pattern, name)

def valid_cluster_version(version):
    """Checks if a given cluster version is valid.
    
    Function Arguments:
       name (string) -- version of the cluster
    
    Returns (bool):
       True  -- if the cluster version is valid
       False -- otherwise
    """
    # We want to match eg. 10, 9.6 but not 9.6.1 or 10.1
    pattern = r"^(\d(\.\d)?|\d{2})$"
    return check_regex(pattern, version)

def get_installed_postgresql_versions():
    """Returns a list of installed PostgreSQL versions.

       Returns (dict):
         key   (string)  -- PostgreSQL version (e.g. 9.6 or 10)
         value (dict)    -- dict containing additional information about this version
                            (e.g. binary path)
    """
    versions = {}
    install_dir = "/usr/lib/postgresql/"

    subdirs = os.listdir(install_dir)

    for version_dir in subdirs:
        initdb_path = os.path.join(*[install_dir, version_dir, "bin", "initdb"])
        if os.path.isfile(initdb_path):
            versions[version_dir] = {}
            versions[version_dir]['binary_path'] = os.path.join(*[install_dir, version_dir, "bin"])

    return versions
