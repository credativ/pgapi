#!/bin/bash

PYTHONPATH=. pytest-3 --cov=pgapi tests --cov-report=html
