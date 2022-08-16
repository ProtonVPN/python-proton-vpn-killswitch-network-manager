#!/usr/bin/env bash
if [[ "$CI" == "true" ]]
then
  sudo mkdir -p /var/run/dbus
  sudo dbus-daemon --config-file=/usr/share/dbus-1/system.conf --print-address
fi

python3 -m pytest tests/integration/test_killswitch_connection.py
