from proton.vpn.killswitch import KillSwitch
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    KillSwitchConfig, KillSwitchConnectionHandler)
from proton.vpn.killswitch.exceptions import KillSwitchError


class NMKillSwitch(KillSwitch):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ks_handler = KillSwitchConnectionHandler()

    def _enable(self, server_ip=None, **_):
        if server_ip:
            self.__update_with_server_ip(server_ip)
        else:
            self.__enable()

    def _disable(self, **_):
        self.__assert_killswitch_connection_exists()

        if self._ks_handler.is_killswitch_connection_active():
            self._ks_handler.remove()
            self.__assert_killswitch_connection_does_not_exists()

    def __enable(self):
        self.__assert_killswitch_connection_does_not_exists()

        if not self._ks_handler.is_killswitch_connection_active():
            self._ks_handler.add()
            self.__assert_killswitch_connection_exists()

    def __update_with_server_ip(self, server_ip, **_):
        self.__assert_killswitch_connection_exists()

        if self._ks_handler.is_killswitch_connection_active():
            self._ks_handler.update(server_ip)

    def __assert_killswitch_connection_exists(self):
        if not self._ks_handler.is_killswitch_connection_active():
            raise KillSwitchError(
                "Kill switch connection {} could not be found".format(
                    KillSwitchConfig.interface_name
                )
            )

    def __assert_killswitch_connection_does_not_exists(self):
        if self._ks_handler.is_killswitch_connection_active():
            raise KillSwitchError(
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
