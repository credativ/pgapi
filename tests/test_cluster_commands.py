#!/usr/bin/env python3

from pgapi.helper import Config
from pgapi.clusterCommands import *

from types import *

# config = Config.getInstnace()

# config.setSetting("parameters", "use_sudo", True)
# config.setSetting("parameters", "sudo_user", "postgres")

def test_sudo_prefix():
    sudo_prefix_str = sudo_prefix()
    assert sudo_prefix_str == "sudo -u postgres"

def test_cluster_get_returns_list():
    c = cluster_get_all()
    assert isinstance(c, list)

def test_cluster_get_returns_list():
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
    c = cluster_get('9.5', 'main')
    assert isinstance(c, list)

def test_cluster_get_param_version():
    c = cluster_get('9.5')
    assert isinstance(c, list)

def test_cluster_get_param_name():
    c = cluster_get(name='main')
    assert isinstance(c, list)

def test_cluster_get_setting():
    # FIXME: The following test assumes there is a 9.6/main cluster.
    c = cluster_get_setting('9.5', 'main', 'port')
    assert isinstance(c, str)

def test_cluster_create():
    (rc, out, err) = cluster_create('9.5', 'pgapi_test')
    assert err == ""
    assert 0 == rc

def test_cluster_set_setting():
    (rc, out, err) = cluster_set_setting('9.5', 'pgapi_test', 'log_connections', 'on')
    assert err == ""
    assert 0 == rc

def test_verify_setting():
    setting = cluster_get_setting('9.5', 'pgapi_test', 'log_connections')
    assert setting == 'on'

# def test_start_cluster():
#     (rc, out, err) = ctl_cluster('9.5', 'pgapi_test', 'start')
#     assert err == ""
#     assert 0 == rc

# def test_stop_cluster():
#     (rc, out, err) = ctl_cluster('9.5', 'pgapi_test', 'stop')
#     assert err == ""
#     assert 0 == rc

def test_cluster_drop():
    (rc, out, err) = cluster_drop('9.5', 'pgapi_test')
    assert err == ""
    assert 0 == rc
