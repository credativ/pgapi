#!/usr/bin/env python3

from pgapi.helper import *

def test_param_is_safe_1_true():
    assert True == param_is_safe('port')

def test_param_is_safe_2_true():
    assert True == param_is_safe('archive_command')

def test_param_is_safe_1_false():
    assert False == param_is_safe('_')

def test_valid_cluster_version_1_true():
    assert True == valid_cluster_version('9.6')

def test_valid_cluster_version_2_true():
    assert True == valid_cluster_version('10')

def test_valid_cluster_version_1_false():
    assert False == valid_cluster_version('9.6.1')

def test_valid_cluster_version_2_false():
    assert False == valid_cluster_version('10.1')

def test_valid_cluster_version_3_false():
    assert False == valid_cluster_version('10;')

def test_valid_cluster_name_1_true():
    assert True == valid_cluster_name('main')

def test_valid_cluster_name_2_true():
    assert True== valid_cluster_name('test-1')

def test_valid_cluster_name_3_true():
    assert True== valid_cluster_name('test_1')

def test_valid_cluster_name_1_false():
    assert False == valid_cluster_name('123test')

def test_valid_cluster_name_2_false():
    assert False == valid_cluster_name('test;')
    
def test_valid_cluster_name_3_false():
    assert False == valid_cluster_name('test&&')
