import logging

from proton.vpn.killswitch import KillSwitch
from proton.vpn.killswitch
from proton.vpn.killswitch import (
    KillSwitchConfig, KillSwitchConnectionHandler)
from proton.vpn.killswitch.interface.exceptions import KillSwitchException

logger = logging.getLogger(__name__)


class NMKillSwitch(KillSwitch):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ks_handler = KillSwitchConnectionHandler()

    def _enable(self, server_ip=None, **_):
        if not self._ks_handler.is_killswitch_connection_active():
            self._ks_handler.add()
        if server_ip:
            self._ks_handler.update(server_ip)

        self.__assert_killswitch_connection_exists()

    def _disable(self, **_):
        self._ks_handler.remove()
        self.__assert_killswitch_connection_does_not_exists()

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
