import logging

from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    KillSwitchConfig, KillSwitchConnectionHandler)
from proton.vpn.killswitch.interface import KillSwitch
from proton.vpn.killswitch.interface.exceptions import KillSwitchException

logger = logging.getLogger(__name__)


class NMKillSwitch(KillSwitch):

    def __init__(self, state, ks_handler=None):
        self._ks_handler = ks_handler or KillSwitchConnectionHandler()
        super().__init__(state)

    def _enable(self, ipv4_serverip=None, **_):
        if not self._ks_handler.is_killswitch_connection_active():
            self._ks_handler.add()
            if ipv4_serverip:
                self._ks_handler.update(ipv4_serverip)

        self.__assert_killswitch_connection_exists()

    def _disable(self, **_):
        if self._ks_handler.is_killswitch_connection_active():
            self._ks_handler.remove()
            self.__assert_killswitch_connection_does_not_exists()

    def _update(self, ipv4_server=None, **_):
        self.__assert_killswitch_connection_exists()
        self._ks_handler.update(ipv4_server)

    def __assert_killswitch_connection_exists(self):
        if not self._ks_handler.is_killswitch_connection_active():
            raise KillSwitchException(
                "Kill switch connection {} could not be found".format(
                    KillSwitchConfig.interface_name
                )
            )

    def __assert_killswitch_connection_does_not_exists(self):
        if self._ks_handler.is_killswitch_connection_active():
            raise KillSwitchException(
                "Kill switch connection {} was found".format(
                    KillSwitchConfig.interface_name
                )
            )

    @classmethod
    def _get_priority(cls) -> int:
        return 100

    @classmethod
    def _validate(cls):
        return True
