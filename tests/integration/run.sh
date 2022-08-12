#!/usr/bin/env bash

export $(dbus-launch)
python3 -m pytest tests/integration/test_killswitch_connection.py