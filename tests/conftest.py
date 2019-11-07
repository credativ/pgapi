from pgapi.helper import Config
from pgapi.clusterAPI import *
from pgapi.server import ServerAPI

import pytest


@pytest.fixture(scope='session')
def test_client():
    config = Config.getInstance()
    config.setSetting("arguments","use_sudo",True)
    config.setSetting("arguments", "sudo_user", 'postgres')
    config.setSetting("arguments","debug",True)
    SA = ServerAPI()
    SA.setup(config)
    testing_client = SA.server_app.test_client()
 
    # Establish an application context before running the tests.
    ctx = SA.server_app.app_context()
    ctx.push()
 
    yield testing_client  # this is where the testing happens!
 
    ctx.pop()