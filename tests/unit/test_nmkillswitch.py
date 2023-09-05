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


def test_sucessfully_enable_full_killswitch_and_remove_routed_killswitch_connection():
    future_mock = Future()
    future_mock.set_result(None)

    ks_handler_mock = Mock()
    ks_handler_mock.add_full_killswitch_connection.return_value = future_mock
    ks_handler_mock.remove_routed_killswitch_connection.return_value = future_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.enable()
    future.result()

    assert len(ks_handler_mock.method_calls) == 2
    ks_handler_mock.add_full_killswitch_connection.assert_called_once_with()
    ks_handler_mock.remove_routed_killswitch_connection.assert_called_once_with()


def test_sucessfully_enable_routed_killswitch_and_remove_full_killswitch(vpn_server):
    future_mock = Future()
    future_mock.set_result(None)

    ks_handler_mock = Mock()
    ks_handler_mock.add_full_killswitch_connection.return_value = future_mock
    ks_handler_mock.remove_routed_killswitch_connection.return_value = future_mock
    ks_handler_mock.add_routed_killswitch_connection.return_value = future_mock
    ks_handler_mock.remove_full_killswitch_connection.return_value = future_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.enable(vpn_server)
    future.result()

    assert len(ks_handler_mock.method_calls) == 4
    ks_handler_mock.add_routed_killswitch_connection.assert_called_once_with(vpn_server.server_ip)
    ks_handler_mock.remove_full_killswitch_connection.assert_called_once_with()


def test_enable_killswitch_raises_exception_when_full_killswitch_connection_can_not_be_created():
    future_mock = Future()
    future_mock.set_exception(GLib.GError)

    ks_handler_mock = Mock()
    ks_handler_mock.add_full_killswitch_connection.return_value = future_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.enable()

    with pytest.raises(KillSwitchException):
        future.result()


def test_enable_killswitch_raises_exception_when_routed_killswitch_connection_can_not_be_removed():
    future_mock_with_exception = Future()
    future_mock_with_exception.set_exception(GLib.GError)

    future_mock_with_success = Future()
    future_mock_with_success.set_result(None)

    ks_handler_mock = Mock()
    ks_handler_mock.add_full_killswitch_connection.return_value = future_mock_with_success
    ks_handler_mock.remove_routed_killswitch_connection.return_value = future_mock_with_exception

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.enable()

    with pytest.raises(KillSwitchException):
        future.result()


def test_enable_killswitch_raises_exception_when_routed_killswitch_connection_can_not_be_created(vpn_server):
    future_mock_with_exception = Future()
    future_mock_with_exception.set_exception(GLib.GError)

    future_mock_with_success = Future()
    future_mock_with_success.set_result(None)

    ks_handler_mock = Mock()
    ks_handler_mock.add_full_killswitch_connection.return_value = future_mock_with_success
    ks_handler_mock.remove_routed_killswitch_connection.return_value = future_mock_with_success
    ks_handler_mock.add_routed_killswitch_connection.return_value = future_mock_with_exception

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.enable(vpn_server)

    with pytest.raises(KillSwitchException):
        future.result()


def test_enable_killswitch_raises_exception_when_full_killswitch_connection_can_not_be_removed(vpn_server):
    future_mock_with_exception = Future()
    future_mock_with_exception.set_exception(GLib.GError)

    future_mock_with_success = Future()
    future_mock_with_success.set_result(None)

    ks_handler_mock = Mock()
    ks_handler_mock.add_full_killswitch_connection.return_value = future_mock_with_success
    ks_handler_mock.remove_routed_killswitch_connection.return_value = future_mock_with_success
    ks_handler_mock.add_routed_killswitch_connection.return_value = future_mock_with_success
    ks_handler_mock.remove_full_killswitch_connection.return_value = future_mock_with_exception

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.enable(vpn_server)

    with pytest.raises(KillSwitchException):
        future.result()


def test_successfully_disable_kilswitch():
    future_mock = Future()
    future_mock.set_result(None)

    ks_handler_mock = Mock()
    ks_handler_mock.remove_full_killswitch_connection.return_value = future_mock
    ks_handler_mock.remove_routed_killswitch_connection.return_value = future_mock

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.disable()
    future.result()

    assert len(ks_handler_mock.method_calls) == 2
    ks_handler_mock.remove_full_killswitch_connection.assert_called_once()
    ks_handler_mock.remove_routed_killswitch_connection.assert_called_once()


def test_disable_kilswitch_raises_exception_when_full_killswitch_connection_can_not_be_removed():
    future_mock_with_exception = Future()
    future_mock_with_exception.set_exception(GLib.GError)

    ks_handler_mock = Mock()
    ks_handler_mock.remove_full_killswitch_connection.return_value = future_mock_with_exception

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.disable()

    with pytest.raises(KillSwitchException):
        future.result()


def test_disable_kilswitch_raises_exception_when_full_killswitch_connection_can_not_be_removed():
    future_mock_with_exception = Future()
    future_mock_with_exception.set_exception(GLib.GError)

    future_mock_with_success = Future()
    future_mock_with_success.set_result(None)

    ks_handler_mock = Mock()
    ks_handler_mock.remove_full_killswitch_connection.return_value = future_mock_with_success
    ks_handler_mock.remove_routed_killswitch_connection.return_value = future_mock_with_exception

    nm_killswitch = NMKillSwitch(ks_handler_mock)
    future = nm_killswitch.disable()

    with pytest.raises(KillSwitchException):
        future.result()


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


def test_enable_ipv6_leak_protection_raises_exception_when_ipv6_connection_is_not_created():
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


def test_disable_ipv6_leak_protection_raises_exception_when_ipv6_connection_can_not_be_removed():
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
