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
from concurrent.futures import Future
from proton.vpn import logging
from proton.vpn.killswitch.backend.linux.networkmanager.nmclient import NMClient
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    KillSwitchConnection, KillSwitchGeneralConfig, KillSwitchIPConfig
)

logger = logging.getLogger(__name__)

HUMAN_READABLE_ID = "pvpn-killswitch"
INTERFACE_NAME = "pvpnksintrf0"

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
    def is_killswitch_connection_active(self) -> bool:
        """Returns if general kill switch is active or not."""
        return False

    def add(self, server_ip: str):
        """Adds general kill switch to NetworkManager"""
        raise NotImplementedError

    def remove(self):
        """Removes general kill switch from NetworkManager."""
        raise NotImplementedError

    def update(self, server_ip: str):
        """Update the general kill switch."""
        raise NotImplementedError

    @property
    def is_ipv6_leak_protection_connection_active(self) -> bool:
        """Returns if IPv6 kill switch is active or not."""
        return bool(self.nm_client.get_active_connection(IPV6_HUMAN_READABLE_ID))

    def add_ipv6_leak_protection(self) -> Future:
        """Adds IPv6 kill switch to NetworkManager."""
        general_config = KillSwitchGeneralConfig(
            human_readable_id=IPV6_HUMAN_READABLE_ID,
            interface_name=IPV6_INTERFACE_NAME
        )

        ipv6_config = KillSwitchIPConfig(
            addresses=["fdeb:446c:912d:08da::/64"],
            dns=["::1"],
            dns_priority=-1400,
            gateway="fdeb:446c:912d:08da::1",
            ignore_auto_dns=True,
            route_metric=97
        )
        killswitch = KillSwitchConnection(
            general_config,
            ipv6_settings=ipv6_config
        )
        future = self.nm_client.add_connection_async(killswitch.connection)
        return future

    def remove_ipv6_leak_protection(self) -> Future:
        """Removes IPv6 kill switch from NetworkManager."""
        connection = self.nm_client.get_connection(conn_id=IPV6_HUMAN_READABLE_ID)
        future = self.nm_client.remove_connection_async(connection)
        return future
