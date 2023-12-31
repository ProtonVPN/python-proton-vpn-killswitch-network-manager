"""
This modules contains the classes that communicate with NetworkManager.


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
from ipaddress import ip_network
from concurrent.futures import Future
from proton.vpn import logging
from proton.vpn.killswitch.backend.linux.networkmanager.nmclient import NMClient
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    KillSwitchConnection, KillSwitchGeneralConfig, KillSwitchIPConfig
)

logger = logging.getLogger(__name__)

IPV4_HUMAN_READABLE_ID = "pvpn-killswitch"
IPV4_INTERFACE_NAME = "pvpnksintrf0"

IPV4_ROUTED_HUMAN_READABLE_ID = "pvpn-routed-killswitch"
IPV4_ROUTED_INTERFACE_NAME = "pvpnrouteintrf0"

IPV6_HUMAN_READABLE_ID = "pvpn-killswitch-ipv6"
IPV6_INTERFACE_NAME = "ipv6leakintrf0"


class KillSwitchConnectionHandler:
    """Kill switch connection management."""

    def __init__(self, nm_client: NMClient = None):
        self._nm_client = nm_client

    @property
    def nm_client(self):
        """Returns the NetworkManager client."""
        if self._nm_client is None:
            self._nm_client = NMClient()

        return self._nm_client

    @property
    def is_network_manager_running(self) -> bool:
        """Returns if the Network Manager daemon is running or not."""
        return self.nm_client.get_nm_running()

    @property
    def is_connectivity_check_enabled(self) -> bool:
        """Returns if connectivity_check property is enabled or not."""
        return self.nm_client.connectivity_check_get_enabled()

    @property
    def is_ipv6_leak_protection_connection_active(self) -> bool:
        """Returns if IPv6 kill switch is active or not."""
        return bool(self.nm_client.get_active_connection(IPV6_HUMAN_READABLE_ID))

    @property
    def is_full_killswitch_connection_active(self) -> bool:
        """Returns if full kill switch is active or not."""
        return bool(self.nm_client.get_active_connection(IPV6_HUMAN_READABLE_ID))

    @property
    def is_routed_killswitch_connection_active(self) -> bool:
        """Returns if routed kill switch is active or not."""
        return bool(self.nm_client.get_active_connection(IPV4_ROUTED_HUMAN_READABLE_ID))

    def add_full_killswitch_connection(self) -> Future:
        """Adds full kill switch connection to Network Manager. This connection blocks all
        outgoing traffic when not connected to VPN, with the exception of torrent client which will
        require to be bonded to the VPN interface.."""
        self._ensure_connectivity_check_is_disabled()

        connection = self.nm_client.get_active_connection(
            conn_id=IPV4_HUMAN_READABLE_ID)

        if connection:
            future = Future()
            future.set_result(None)
            return future

        general_config = KillSwitchGeneralConfig(
            human_readable_id=IPV4_HUMAN_READABLE_ID,
            interface_name=IPV4_INTERFACE_NAME
        )

        ipv4_config = KillSwitchIPConfig(
            addresses=["100.85.0.1/24"],
            dns=["0.0.0.0"],
            dns_priority=-1400,
            gateway="100.85.0.1",
            ignore_auto_dns=True,
            route_metric=98
        )
        killswitch = KillSwitchConnection(
            general_config,
            ipv4_settings=ipv4_config,
            ipv6_settings=None,
        )
        future = self.nm_client.add_connection_async(killswitch.connection)
        return future

    def add_routed_killswitch_connection(self, server_ip: str):
        """Add routed kill switch connection to Network Manager.

        This connection has a "hole punched in it", to allow only the server IP to
        access the outside world while blocking all other outgoing traffic. This is only
        temporary though as it will be removed once we establish a VPN connection and will
        get replaced by the full kill switch connection.
        """
        self._ensure_connectivity_check_is_disabled()

        subnet_list = list(ip_network('0.0.0.0/0').address_exclude(
            ip_network(server_ip)
        ))

        general_config = KillSwitchGeneralConfig(
            human_readable_id=IPV4_ROUTED_HUMAN_READABLE_ID,
            interface_name=IPV4_ROUTED_INTERFACE_NAME
        )
        ipv4_config = KillSwitchIPConfig(
            addresses=["100.85.0.1/24"],
            dns=["0.0.0.0"],
            dns_priority=-1400,
            ignore_auto_dns=True,
            route_metric=97,
            routes=subnet_list
        )
        killswitch = KillSwitchConnection(
            general_config,
            ipv4_settings=ipv4_config,
            ipv6_settings=None,
        )
        future = self.nm_client.add_connection_async(killswitch.connection)
        return future

    def add_ipv6_leak_protection(self) -> Future:
        """Adds IPv6 kill switch to NetworkManager. This connection is mainly
        to prevent IPv6 leaks while using IPv4."""
        self._ensure_connectivity_check_is_disabled()

        connection = self.nm_client.get_active_connection(
            conn_id=IPV4_HUMAN_READABLE_ID)

        if connection:
            future = Future()
            future.set_result(None)
            return future

        general_config = KillSwitchGeneralConfig(
            human_readable_id=IPV6_HUMAN_READABLE_ID,
            interface_name=IPV6_INTERFACE_NAME
        )

        ip_config = KillSwitchIPConfig(
            addresses=["fdeb:446c:912d:08da::/64"],
            dns=["::1"],
            dns_priority=-1400,
            gateway="fdeb:446c:912d:08da::1",
            ignore_auto_dns=True,
            route_metric=95
        )
        killswitch = KillSwitchConnection(
            general_config,
            ipv4_settings=None,
            ipv6_settings=ip_config,
        )
        future = self.nm_client.add_connection_async(killswitch.connection)
        return future

    def remove_full_killswitch_connection(self) -> Future:
        """Removes full kill switch connection."""
        return self._remove_connection(IPV4_HUMAN_READABLE_ID)

    def remove_routed_killswitch_connection(self) -> Future:
        """Removes routed kill switch connection."""
        return self._remove_connection(IPV4_ROUTED_HUMAN_READABLE_ID)

    def remove_ipv6_leak_protection(self) -> Future:
        """Removes IPv6 kill switch connection."""
        return self._remove_connection(IPV6_HUMAN_READABLE_ID)

    def _remove_connection(self, connection_id: str) -> Future:
        connection = self.nm_client.get_connection(
            conn_id=connection_id)

        logger.debug(f"Attempting to remove {connection_id}: {connection}")

        if connection is None:
            logger.debug(f"There was no {connection_id} to remove: {connection}")
            future = Future()
            future.set_result(None)
            return future

        future = self.nm_client.remove_connection_async(connection)
        return future

    def _ensure_connectivity_check_is_disabled(self):
        def _disable_connectivity_check_finish(_future: Future):
            _future.result()

        if self.is_connectivity_check_enabled:
            future = self.nm_client.disable_connectivity_check()
            future.add_done_callback(_disable_connectivity_check_finish)
