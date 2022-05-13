from proton.vpn.killswitch import KillSwitch
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    KillSwitchConnectionHandler, KillSwitchConfig)
from proton.vpn.killswitch.enums import KillSwitchStateEnum
from proton.vpn.killswitch.exceptions import (KillSwitchStartError,
                                              KillSwitchStopError,
                                              UnexpectedKillSwitchStateError)


class NMKillSwitch(KillSwitch):
    ATTEMPTS = 5

    @property
    def _ks_handler(self):
        try:
            if self.__ks_handler is None:
                self.__ks_handler = KillSwitchConnectionHandler()
        except AttributeError:
            self.__ks_handler = KillSwitchConnectionHandler()

        return self.__ks_handler

    def _on_disconnected(self, **kwargs):
        if (
            self.state == KillSwitchStateEnum.ON and not self.permanent_mode
        ) or self.state == KillSwitchStateEnum.OFF:
            self._disable()
        else:
            self._enable()

    def _on_connecting(self, **kwargs):
        if (
            self.state == KillSwitchStateEnum.ON and not self.permanent_mode
        ) or self.state == KillSwitchStateEnum.OFF:
            self._disable()
        else:
            key = "server_ip"
            if key not in kwargs:
                raise KeyError("Missing key `{}`".format(key))

            value = kwargs.get(key)
            if value is None:
                raise TypeError("Missing value for key `{}`".format(key))

            self._enable(value)

    def _on_connected(self, **kwargs):
        if self.state == KillSwitchStateEnum.ON:
            self._enable()
        else:
            self._disable()

    def _disable(self):
        self.__attempt_to_delete_killswitch_connection(KillSwitchConfig())

    def _enable(self, server_ip=False):
        if server_ip:
            killswitch_config = KillSwitchConfig(server_ip)
        else:
            killswitch_config = KillSwitchConfig()

        self.__attempt_to_activate_killswitch(killswitch_config)

    def __attempt_to_activate_killswitch(self, killswitch_config: KillSwitchConfig):
        """
            :raises KillSwitchStartError: If unable to start kill switch connection
        """
        attempts = self.ATTEMPTS

        while attempts > 0:
            try:
                self.__ensure_killswitch_connection_exists()
            except UnexpectedKillSwitchStateError:
                pass
            else:
                break

            try:
                self._ks_handler.add(killswitch_config)
            except KillSwitchStartError:
                pass

            attempts -= 1

        try:
            self.__ensure_killswitch_connection_exists()
        except UnexpectedKillSwitchStateError:
            raise KillSwitchStartError(
                "Unable to start kill switch with interface {}. Check NetworkManager syslogs".format(
                    killswitch_config.interface_name
                )
            )

    def __attempt_to_delete_killswitch_connection(self):
        """
            :raises KillSwitchStartError: If unable to stop kill switch connection
        """
        attempts = self.ATTEMPTS

        while self.ATTEMPTS > 0:
            try:
                self.__ensure_killswitch_connection_exists()
            except UnexpectedKillSwitchStateError:
                break

            try:
                self._ks_handler.remove(KillSwitchConfig.interface_name)
            except KillSwitchStopError:
                pass

            attempts -= 1

        try:
            self.__ensure_killswitch_connection_exists()
        except UnexpectedKillSwitchStateError:
            pass
        else:
            raise KillSwitchStopError(
                "Unable to stop kill switch with interface {}. Check NetworkManager syslogs".format(
                    KillSwitchConfig.interface_name
                )
            )

    def __ensure_killswitch_connection_exists(self):
        if not self._ks_handler.is_killswitch_connection_active(KillSwitchConfig.interface_name):
            raise UnexpectedKillSwitchStateError(
                "Kill switch connection {} could not be found".format(
                    KillSwitchConfig.interface_name
                )
            )

    @classmethod
    def _get_priority(cls) -> int:
        return 100

    @classmethod
    def _validate(cls):
        return True
