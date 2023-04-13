"""
Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
from unittest.mock import Mock, PropertyMock, patch
from concurrent.futures import Future
import pytest

from proton.vpn.killswitch.backend.linux.networkmanager.nmclient import GLib
from proton.vpn.killswitch.backend.linux.networkmanager import NMKillSwitch
from proton.vpn.killswitch.interface.exceptions import KillSwitchException


@pytest.fixture
def vpn_server():
    vpn_server_mock = Mock()
    vpn_server_mock.server_ip = "1.1.1.1"

    return vpn_server_mock


def test_sucessfully_enable_killswitch(vpn_server):
    ks_handler_mock = Mock()
    is_killswitch_connection_active_mock = PropertyMock(side_effect=[False, True])
    type(ks_handler_mock).is_killswitch_connection_active = is_killswitch_connection_active_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    nm_killswitch.enable(vpn_server)

    ks_handler_mock.add.assert_called_once_with(vpn_server.server_ip)


def test_enable_killswitch_raises_exception_when_killswitch_is_not_active_after_being_enabled(vpn_server):
    ks_handler_mock = Mock()
    is_killswitch_connection_active_mock = PropertyMock(side_effect=[False, False])
    type(ks_handler_mock).is_killswitch_connection_active = is_killswitch_connection_active_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)

    with pytest.raises(KillSwitchException):
        nm_killswitch.enable(vpn_server)


def test_sucessfully_disable_killswitch():
    ks_handler_mock = Mock()
    is_killswitch_connection_active_mock = PropertyMock(side_effect=[True, False])
    type(ks_handler_mock).is_killswitch_connection_active = is_killswitch_connection_active_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    nm_killswitch.disable()

    ks_handler_mock.remove.assert_called_once()


def test_disable_killswitch_raises_exception_when_killswitch_is_active_after_being_disabled():
    ks_handler_mock = Mock()
    is_killswitch_connection_active_mock = PropertyMock(side_effect=[True, True])
    type(ks_handler_mock).is_killswitch_connection_active = is_killswitch_connection_active_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)

    with pytest.raises(KillSwitchException):
        nm_killswitch.disable()


def test_sucessfully_enable_ipv6_leak_protection():
    future_mock = Future()
    future_mock.set_result(None)
    ks_handler_mock = Mock()
    ks_handler_mock.add_ipv6_leak_protection.return_value = future_mock
    is_ipv6_leak_protection_connection_active_mock = PropertyMock(side_effect=[False])
    type(ks_handler_mock).is_ipv6_leak_protection_connection_active = is_ipv6_leak_protection_connection_active_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.enable_ipv6_leak_protection()
    future.result()

    ks_handler_mock.add_ipv6_leak_protection.assert_called_once()


def test_enable_ipv6_leak_protection_raises_exception_when_ipv6_killswitch_is_not_active_after_being_enabled():
    future_mock = Future()
    future_mock.set_exception(GLib.GError)
    ks_handler_mock = Mock()
    ks_handler_mock.add_ipv6_leak_protection.return_value = future_mock
    is_killswitch_connection_active_mock = PropertyMock(side_effect=[False])
    type(ks_handler_mock).is_ipv6_leak_protection_connection_active = is_killswitch_connection_active_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.enable_ipv6_leak_protection()

    with pytest.raises(KillSwitchException):
        future.result()

def test_sucessfully_disable_ipv6_leak_protection():
    future_mock = Future()
    future_mock.set_result(None)
    ks_handler_mock = Mock()
    ks_handler_mock.remove_ipv6_leak_protection.return_value = future_mock
    is_ipv6_leak_protection_connection_active_mock = PropertyMock(side_effect=[True])
    type(ks_handler_mock).is_ipv6_leak_protection_connection_active = is_ipv6_leak_protection_connection_active_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.disable_ipv6_leak_protection()
    future.result()

    ks_handler_mock.remove_ipv6_leak_protection.assert_called_once()


def test_disable_ipv6_leak_protection_raises_exception_when_ipv6_killswitch_is_active_after_being_disabled():
    future_mock = Future()
    future_mock.set_exception(GLib.GError)
    ks_handler_mock = Mock()
    ks_handler_mock.remove_ipv6_leak_protection.return_value = future_mock
    is_killswitch_connection_active_mock = PropertyMock(side_effect=[True])
    type(ks_handler_mock).is_ipv6_leak_protection_connection_active = is_killswitch_connection_active_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.disable_ipv6_leak_protection()

    with pytest.raises(KillSwitchException):
        future.result()