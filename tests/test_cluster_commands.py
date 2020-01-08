#!/usr/bin/env python3

from pgapi.helper import Config
from pgapi.clusterCommands import *

import os
from types import *

# config = Config.getInstnace()

# config.setSetting("parameters", "use_sudo", True)
# config.setSetting("parameters", "sudo_user", "postgres")


def test_sudo_prefix():
    sudo_prefix_str = sudo_prefix()
    assert sudo_prefix_str == "sudo -u postgres"


def test_cluster_get_all_returns_list():
    c = cluster_get_all()
    assert isinstance(c, list)


def test_cluster_get_contains_dict():
    c = cluster_get_all()
    for cluster in c:
        assert isinstance(cluster, dict)


def test_cluster_get_empty():
    c = cluster_get('1.0', 'main')
    assert c == []


def get_cluster_get_invalid_version():
    c = cluster_get('1.0')
    assert c == []


def test_cluster_get_returns_list():
    c = cluster_get()
    assert isinstance(c, list)


def test_cluster_get_param():
    c = cluster_get('9.6', 'main')
    assert isinstance(c, list)


def test_cluster_get_param_version():
    c = cluster_get('9.6')
    assert isinstance(c, list)


def test_cluster_get_param_name():
    c = cluster_get(name='main')
    assert isinstance(c, list)


def test_cluster_del_no_autostart(test_client):
    # Try to stop it. Don't care if it allready is
    test_client.patch('/cluster/11/demo', data={"state": "stop"})
    r = test_client.delete('/cluster/11/demo')
    assert r.status_code == 200 or r.status_code == 404


def test_cluster_create_no_autostart(test_client):
    r = test_client.post('/cluster/11/demo', data={"port": "5444"})
    assert r.status_code == 201 or r.status_code == 409


def test_cluster_get_setting(test_client):
    r = test_client.get('/cluster/11/demo')
    assert r.json['config']['port'] == '5444'


def test_cluster_get_broken():
    oldpath = os.environ['PATH']
    try:
        os.environ['PATH'] = '.'
        c = cluster_get_all()
        assert False
    except Exception:
        os.environ['PATH'] = oldpath
        assert True


def test_cluster_start(test_client):
    r = test_client.patch('/cluster/11/demo', data={'state': 'start'})
    assert r.status_code == 200


def test_cluster_stop_validate(test_client):
    r = test_client.get('/cluster/11/demo')
    assert r.status_code.json['state'] == '1'


def test_cluster_stop(test_client):
    r = test_client.patch('/cluster/11/demo', data={'state': 'start'})
    assert r.status_code == 200


def test_cluster_stop_validate_patch(test_client):
    r = test_client.patch('/cluster/11/demo', data={'state': 'stop'})
    assert r.status_code == 200


def test_cluster_set_setting(test_client):
    r = test_client.patch('/cluster/11/demo',
                          data=json.dumps({'config': {'max_wal_size': '2GB'}}),
                          content_type="application/json")
    assert r.status_code == 200
    r = test_client.get('/cluster/11/demo')
    print(r.json)
    assert r.json['config']['max_wal_size'] == '2GB'



# def test_start_cluster():
#     (rc, out, err) = ctl_cluster('9.6', 'pgapi_test', 'start')
#     assert err == ""
#     assert 0 == rc

# def test_stop_cluster():
#     (rc, out, err) = ctl_cluster('9.6', 'pgapi_test', 'stop')
#     assert err == ""
#     assert 0 == rc

def test_nonexistent_dbversion(test_client):
    # 8.5 is not a valid postgresql release.
    r = test_client.post('/cluster/8.5/pgapi_test')
    assert r.status_code == 500


def test_drop_nonexistent_db():
    (rc, out, err) = cluster_drop('9.6', 'pgapi_testXXXXXXXXXXX')
    assert err[:-1] == 'Error: specified cluster does not exist'
    assert 1 == rc


def test_weird_action():
    try:
        # 8.5 is not a valid postgresql release.
        (rc, out, err) = cluster_ctl('8.5', 'pgapi_test', 'XXXXXX')
        assert False
    except Exception as e:
        assert str(
            e) == "Action has to be one of ['start', 'stop', 'restart', 'reload', 'promote', 'status']"
