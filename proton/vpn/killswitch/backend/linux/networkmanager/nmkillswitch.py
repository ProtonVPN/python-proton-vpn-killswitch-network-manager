"""
Module for Kill Switch based on Network Manager.


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
import sys
from concurrent.futures import Future

from gi.repository import GLib

from proton.vpn.killswitch.interface import KillSwitch
from proton.vpn.killswitch.interface.exceptions import KillSwitchException
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection_handler\
    import KillSwitchConnectionHandler
from proton.vpn import logging


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

    def enable(self, vpn_server: "VPNServer" = None):  # noqa
        """Enables general kill switch."""
        custom_future = Future()

        def on_add_full_killswitch_connection_finish(add_full_ks_future: Future):
            def on_remove_routed_killswitch_connection_finish(remove_routed_ks_future: Future):
                def on_add_routed_killswitch_finish(add_routed_ks_future: Future):
                    def on_remove_full_killswitch_finish(remove_full_ks_future: Future):
                        try:
                            remove_full_ks_future.result()
                            custom_future.set_result(None)
                            logger.debug("No issue removing full kill switch during ENABLE")
                        except GLib.GError as excp:
                            traceback = sys.exc_info()[2]
                            custom_future.set_exception(
                                KillSwitchException(
                                    f"Unable to remove full kill switch: {excp}"
                                ).with_traceback(traceback)
                            )
                    try:
                        add_routed_ks_future.result()
                        logger.debug("No issue adding routed kill switch during ENABLE")
                    except GLib.GError as excp:
                        traceback = sys.exc_info()[2]
                        custom_future.set_exception(
                            KillSwitchException(
                                f"Unable to add routed kill switch connection: {excp}"
                            ).with_traceback(traceback)
                        )
                    else:
                        remove_full_ks_future = self._ks_handler.remove_full_killswitch_connection()
                        remove_full_ks_future.add_done_callback(
                            on_remove_full_killswitch_finish)

                add_routed = vpn_server and vpn_server.server_ip

                try:
                    remove_routed_ks_future.result()
                    logger.debug("No issue removing routed kill switch during ENABLE")
                    if not add_routed:
                        custom_future.set_result(None)
                except GLib.GError as excp:
                    traceback = sys.exc_info()[2]
                    custom_future.set_exception(
                        KillSwitchException(
                            f"Unable to remove routed kill switch connection: {excp}"
                        ).with_traceback(traceback)
                    )
                else:
                    if add_routed:
                        add_routed_ks_future = self._ks_handler.add_routed_killswitch_connection(
                            vpn_server.server_ip)
                        add_routed_ks_future.add_done_callback(
                            on_add_routed_killswitch_finish)

            try:
                add_full_ks_future.result()
                logger.debug("No issue adding full kill switch during ENABLE")
            except GLib.GError as excp:
                traceback = sys.exc_info()[2]
                custom_future.set_exception(
                    KillSwitchException(
                        f"Unable to add full kill switch connection: {excp}"
                    ).with_traceback(traceback)
                )
            else:
                remove_routed_ks_future = self._ks_handler.remove_routed_killswitch_connection()
                remove_routed_ks_future.add_done_callback(
                    on_remove_routed_killswitch_connection_finish)

        add_full_ks_future = self._ks_handler.add_full_killswitch_connection()
        add_full_ks_future.add_done_callback(on_add_full_killswitch_connection_finish)

        return custom_future

    def disable(self):
        """Disables general kill switch."""
        custom_future = Future()

        def _on_full_ks_removed(remove_full_ks: Future):
            def _on_routed_ks_removed(remove_routed_ks: Future):
                try:
                    remove_routed_ks.result()
                    logger.debug("No issue removing routed kill switch during DISABLE")
                except GLib.GError as excp:
                    traceback = sys.exc_info()[2]
                    custom_future.set_exception(
                        KillSwitchException(
                            f"Unable to remove routed kill switch: {excp}"
                        ).with_traceback(traceback)
                    )
                else:
                    custom_future.set_result(None)

            try:
                remove_full_ks.result()
                logger.debug("No issue removing full kill switch during DISABLE")
            except GLib.GError as excp:
                traceback = sys.exc_info()[2]
                custom_future.set_exception(
                    KillSwitchException(
                        f"Unable to remove full kill switch: {excp}"
                    ).with_traceback(traceback)
                )
            else:
                remove_routed_ks_future = self._ks_handler.remove_routed_killswitch_connection()
                remove_routed_ks_future.add_done_callback(_on_routed_ks_removed)

        remove_full_ks_future = self._ks_handler.remove_full_killswitch_connection()
        remove_full_ks_future.add_done_callback(_on_full_ks_removed)

        return custom_future

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
