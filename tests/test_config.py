#!/usr/bin/env python3

from pgapi.helper import Config
from types import *

config = Config.getInstance()

def test1():
    assert isinstance(config.getSetting("port"), int)

def test2():
    config.loadConfigFile("tests/pgapi.conf")
    
def test3():
    assert 15432 == config.getSetting("port")

def test4():
    config.setSetting("arguments", "port", 13)
    assert 13 == config.getSetting("port")

def test5():
    assert True is config.getSetting("use_sudo")

def test6():
    assert "postgres" == config.getSetting("sudo_user")
