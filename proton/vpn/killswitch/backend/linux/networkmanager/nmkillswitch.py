"""
Module for Kill Switch based on Network Manager.
"""
import sys
from concurrent.futures import Future

import gi
gi.require_version("NM", "1.0")  # noqa: required before importing NM module
# pylint: disable=wrong-import-position
from gi.repository import GLib # noqa

from proton.vpn.killswitch.interface import KillSwitch # noqa
from proton.vpn.killswitch.interface.exceptions import KillSwitchException # noqa
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection_handler\
    import KillSwitchConnectionHandler # noqa
from proton.vpn import logging # noqa

logger = logging.getLogger(__name__)


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

        if not self._ks_handler.is_killswitch_connection_active:
            raise KillSwitchException("Kill Switch is not running")

    def disable(self):
        """Disables general kill switch."""
        if self._ks_handler.is_killswitch_connection_active:
            self._ks_handler.remove()

        if self._ks_handler.is_killswitch_connection_active:
            raise KillSwitchException("Kill Switch is not running")

    def update(self, vpn_server):
        """Currently not being used"""
        raise NotImplementedError

    def enable_ipv6_leak_protection(self) -> Future:
        """Enables IPv6 kill switch."""
        custom_future = Future()

        if self._ks_handler.is_ipv6_leak_protection_connection_active:
            custom_future.set_result(None)
            return custom_future

        def _on_ivp6_leak_protection_enabled(_future: Future):
            try:
                _future.result()
                custom_future.set_result(None)
            except GLib.GError:
                traceback = sys.exc_info()[2]
                custom_future.set_exception(
                    KillSwitchException(
                        "Unable to add IPv6 connection"
                    ).with_traceback(traceback)
                )

        future = self._ks_handler.add_ipv6_leak_protection()
        future.add_done_callback(_on_ivp6_leak_protection_enabled)
        return custom_future

    def disable_ipv6_leak_protection(self) -> Future:
        """Disables IPv6 kill switch."""
        custom_future = Future()
        if not self._ks_handler.is_ipv6_leak_protection_connection_active:
            custom_future.set_result(None)
            return custom_future

        def _on_ivp6_leak_protection_disabled(_future: Future):
            try:
                _future.result()
                custom_future.set_result(None)
            except GLib.GError:
                traceback = sys.exc_info()[2]
                custom_future.set_exception(
                    KillSwitchException(
                        "Unable to remove IPv6 connection"
                    ).with_traceback(traceback)
                )

        future = self._ks_handler.remove_ipv6_leak_protection()
        future.add_done_callback(_on_ivp6_leak_protection_disabled)
        return custom_future

    @staticmethod
    def _get_priority() -> int:
        return 100

    @staticmethod
    def _validate():
        try:
            return KillSwitchConnectionHandler().is_network_manager_running
        except (ModuleNotFoundError, ImportError):
            return False
