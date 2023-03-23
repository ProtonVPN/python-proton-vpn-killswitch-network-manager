"""
Module for Kill Switch based on Network Manager.
"""
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    KillSwitchConfig, KillSwitchConnectionHandler)
from proton.vpn.killswitch.interface import KillSwitch
from proton.vpn.killswitch.interface.exceptions import KillSwitchException


class NMKillSwitch(KillSwitch):
    """
    Kill Switch implementation using NetworkManager.

    A dummy Network Manager connection is created to redirect non-VPN traffic
    to an invalid IP, therefore blocking it.

    The way it works is that the dummy connection blocking non-VPN traffic is
    added with a lower priority than the VPN connection but with a higher
    priority than the other network manager connections. This way, the routing
    table uses the dummy connection for any traffic that does not go to the
    primary VPN connection.
    """

    def __init__(self, ks_handler: KillSwitchConnectionHandler = None):
        self._ks_handler = ks_handler or KillSwitchConnectionHandler()
        super().__init__()

    def enable(self, vpn_server):
        """Enables general kill switch."""
        if not self._ks_handler.is_killswitch_connection_active:
            # Currently we assume the server IP is and IPv4 address.
            self._ks_handler.add(vpn_server.server_ip)

        self._assert_killswitch_connection_exists(
            self._ks_handler.is_killswitch_connection_active,
            KillSwitchConfig.human_readable_id
        )

    def disable(self):
        """Disables general kill switch."""
        if self._ks_handler.is_killswitch_connection_active:
            self._ks_handler.remove()

        self._assert_killswitch_connection_does_not_exists(
            self._ks_handler.is_killswitch_connection_active,
            KillSwitchConfig.human_readable_id
        )

    def update(self, _):
        """Currently not being used"""
        raise NotImplementedError

    def enable_ipv6_leak_protection(self):
        """Enables IPv6 kill switch."""
        if not self._ks_handler.is_ipv6_leak_protection_connection_active:
            self._ks_handler.add_ipv6_leak_protection()

        self._assert_killswitch_connection_exists(
            self._ks_handler.is_ipv6_leak_protection_connection_active,
            KillSwitchConfig.human_readable_id_ipv6
        )

    def disable_ipv6_leak_protection(self):
        """Disables IPv6 kill switch."""
        if self._ks_handler.is_ipv6_leak_protection_connection_active:
            self._ks_handler.remove_ipv6_leak_protection()

        self._assert_killswitch_connection_does_not_exists(
            self._ks_handler.is_ipv6_leak_protection_connection_active,
            KillSwitchConfig.human_readable_id_ipv6
        )

    def _assert_killswitch_connection_exists(self, connection_exists: bool, conn_name: str):
        if not connection_exists:
            raise KillSwitchException(
                f"Kill switch connection {conn_name} "
                "could not be found"
            )

    def _assert_killswitch_connection_does_not_exists(
        self, connection_exists: bool, conn_name: str
    ):
        if connection_exists:
            raise KillSwitchException(
                f"Kill switch connection {conn_name} was found"
            )

    @classmethod
    def _get_priority(cls) -> int:
        return 100

    @classmethod
    def _validate(cls):
        return True
