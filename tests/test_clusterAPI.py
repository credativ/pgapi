#!/usr/bin/env python3


import os
from types import *

# config = Config.getInstnace()

# config.setSetting("parameters", "use_sudo", True)
# config.setSetting("parameters", "sudo_user", "postgres")

def test_weird_action():
    assert True

def test_cluster(test_client):
    test_client.get('/cluster/')
    assert True

                                #data=dict(email='patkennedy79@gmail.com', password='FlaskIsAwesome'),
                                #follow_redirects=True
def test_create(test_client):
    test_url = '/cluster/11/test'
    c = test_client.post(test_url)
    if (c.status_code == 409): # Singular retry. We might just lack proper cleanup
        print("deleting..")
        assert test_client.delete(test_url).status_code == 200
        assert test_client.post(test_url).status_code == 201
    else:
        assert c.status_code == 201

def test_delete(test_client):
    assert test_client.delete('/cluster/11/test').status_code == 200


