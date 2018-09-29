#!/usr/bin/env python3

from pgapi.helper import Config
from pgapi.clusterAPI import *

import os
from types import *

# config = Config.getInstnace()

# config.setSetting("parameters", "use_sudo", True)
# config.setSetting("parameters", "sudo_user", "postgres")

def test_weird_action():
    assert True

def test_cluster():
    Cluster()
    assert True

def test_create():
    c = Cluster().post('9.6','apitest')
    assert 'apitest' ==c[0]['cluster']

def test_delete():
    Cluster().delete('9.6','apitest')
    assert True


