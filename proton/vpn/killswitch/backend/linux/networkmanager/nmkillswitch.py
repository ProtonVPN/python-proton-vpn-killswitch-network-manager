from proton.vpn.killswitch import KillSwitch
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    BaseKillSwitchConnectionType, FullKillSwitch, RoutedKillSwitch)
from proton.vpn.killswitch.enums import KillSwitchStateEnum
from proton.vpn.killswitch.exceptions import (KillSwitchStartError,
                                              KillSwitchStopError)


class NMKillSwitch(KillSwitch):
    ATTEMPTS = 5

    def _on_disconnected(self, **kwargs):
        if (
            self.state == KillSwitchStateEnum.ON and not self.permanent_mode
        ) or self.state == KillSwitchStateEnum.OFF:
            self.deactivate_killswitch()
        else:
            self.activate_killswitch()

    def _on_connecting(self, **kwargs):
        if (
            self.state == KillSwitchStateEnum.ON and not self.permanent_mode
        ) or self.state == KillSwitchStateEnum.OFF:
            self.deactivate_killswitch()
        else:
            key = "server_ip"
            if key not in kwargs:
                raise KeyError("Missing key `{}`".format(key))

            value = kwargs.get(key)
            if value is None:
                raise TypeError("Missing value for key `{}`".format(key))

            self.activate_routed_killswitch(value)

    def _on_connected(self, **kwargs):
        if self.state == KillSwitchStateEnum.ON:
            self.activate_killswitch()
            self.deactivate_killswitch_that_allows_specific_routes()
        else:
            self.deactivate_killswitch()

    def _on_error(self, **kwargs):
        if self.state == KillSwitchStateEnum.ON:
            self.activate_killswitch()
        else:
            self.deactivate_killswitch()

    def _on_disconnecting(self, **kwargs):
        if self.state == KillSwitchStateEnum.ON:
            self.activate_killswitch()
        else:
            self.deactivate_killswitch()

    def _setup_off(self):
        self.deactivate_killswitch()

    def _setup_killswitch(self):
        self.activate_killswitch()

    def activate_killswitch(self):
        self.__attempt_to_activate_killswitch(FullKillSwitch())

    def activate_routed_killswitch(self, server_ip):
        ks_conn = RoutedKillSwitch()
        ks_conn.ipv4_addresses = self.__format_subnet_list(
            NMKillSwitch.generate_subnet_list(server_ip)
        )
        self.__attempt_to_activate_killswitch(ks_conn)

    def deactivate_killswitch(self):
        self.__attempt_to_delete_killswitch_connection(FullKillSwitch())
        self.__attempt_to_delete_killswitch_connection(RoutedKillSwitch())

    def deactivate_killswitch_that_allows_specific_routes(self):
        self.__attempt_to_delete_killswitch_connection(RoutedKillSwitch())

    def __attempt_to_activate_killswitch(self, ks_conn: BaseKillSwitchConnectionType):
        """
            :param ks_conn: kill switch connection
            :type ks_conn: BaseKillSwitchConnectionType
            :raises KillSwitchStartError: If unable to start kill switch connection
        """
        attempts = self.ATTEMPTS

        while attempts > 0:
            if ks_conn.is_killswitch_connection_active:
                break

            ks_conn.add()
            attempts -= 1

        if not ks_conn.is_killswitch_connection_active:
            raise KillSwitchStartError(
                "Unable to start kill switch with interface {}. Check NetworkManager syslogs".format(
                    ks_conn.interface_name
                )
            )

    def __attempt_to_delete_killswitch_connection(self, ks_conn: BaseKillSwitchConnectionType):
        """
            :param ks_conn: kill switch connection
            :type ks_conn: BaseKillSwitchConnectionType
            :raises KillSwitchStartError: If unable to stop kill switch connection
        """
        attempts = self.ATTEMPTS

        while self.ATTEMPTS > 0:
            if not ks_conn.is_killswitch_connection_active:
                break

            ks_conn.remove()
            attempts -= 1

        if ks_conn.is_killswitch_connection_active:
            raise KillSwitchStopError(
                "Unable to stop kill switch with interface {}. Check NetworkManager syslogs".format(
                    ks_conn.interface_name
                )
            )

    def __format_subnet_list(self, subnet_list):
        """
            :param subnet_list: list with string ip with prefix
                ["192.168.1.2/24", ...]
            :type subnet_list: list(str)
            :return: tuple within list with ip, prefix and gateway
                 properly formatted for dbus connections
            :rtype: list(tuple(str, int, str))
        """
        formatted_data = [
                (
                    route.split("/")[0],
                    int(route.split("/")[1]),
                    route.split("/")[0]
                ) for route in [str(ipv4) for ipv4 in subnet_list]
            ]

        return formatted_data

    @staticmethod
    def generate_subnet_list(server_ip):
        """
            :param server_ip: vpn server ip
            :type server_ip: str
            :return: list with ip that should be included
            :rtype: list(str)
        """
        import ipaddress
        return list(
            ipaddress.ip_network(
                '0.0.0.0/0'
            ).address_exclude(ipaddress.ip_network(server_ip))
        )

    @classmethod
    def _get_priority(cls) -> int:
        return 100

    @classmethod
    def _validate(cls):
        return True
