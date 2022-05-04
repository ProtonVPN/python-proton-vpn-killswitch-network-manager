from proton.vpn.backend.linux.networkmanager.dbus import NetworkManagerBus
from proton.vpn.killswitch import KillSwitch
from proton.vpn.killswitch.enums import KillSwitchStateEnum
from proton.vpn.killswitch.exceptions import (KillSwitchStartError,
                                              KillSwitchStopError)

from .constants import (KILLSWITCH_CONN_NAME, KILLSWITCH_DNS_PRIORITY_VALUE,
                        KILLSWITCH_INTERFACE_NAME, ROUTED_CONN_NAME,
                        ROUTED_INTERFACE_NAME, IPv4_DUMMY_ADDRESS,
                        IPv4_DUMMY_ADDRESS_SUFFIX, IPv4_DUMMY_GATEWAY,
                        IPv6_DUMMY_ADDRESS, IPv6_DUMMY_ADDRESS_SUFFIX,
                        IPv6_DUMMY_GATEWAY)


class NMKillSwitch(KillSwitch):

    ks_conn_name = KILLSWITCH_CONN_NAME
    ks_interface_name = KILLSWITCH_INTERFACE_NAME

    routed_conn_name = ROUTED_CONN_NAME
    routed_interface_name = ROUTED_INTERFACE_NAME

    ipv4_dummy_addrs = IPv4_DUMMY_ADDRESS
    ipv4_dummy_gateway = IPv4_DUMMY_GATEWAY
    ipv4_dummy_suffx = IPv4_DUMMY_ADDRESS_SUFFIX

    ipv6_dummy_addrs = IPv6_DUMMY_ADDRESS
    ipv6_dummy_gateway = IPv6_DUMMY_GATEWAY
    ipv6_dummy_suffx = IPv6_DUMMY_ADDRESS_SUFFIX

    def _on_disconnected(self, **kwargs):
        if (
            self.state == KillSwitchStateEnum.ON and not self.permanent
        ) or self.state == KillSwitchStateEnum.OFF:
            self.__ensure_killswitch_is_not_running()
        else:
            self.__ensure_killswitch_is_running()

    def _on_connecting(self, **kwargs):
        if (
            self.state == KillSwitchStateEnum.ON and not self.permanent
        ) or self.state == KillSwitchStateEnum.OFF:
            self.__ensure_killswitch_is_not_running()
        else:
            key = "server_ip"
            if key not in kwargs:
                raise KeyError("Missing key `{}`".format(key))

            value = kwargs.get(key)
            if value is None:
                raise TypeError("Missing value for key `{}`".format(key))

            self.__ensure_killswitch_only_allows_specific_routes(value)

    def _on_connected(self, **kwargs):
        if self.state == KillSwitchStateEnum.ON and (self.permanent or not self.permanent):
            self.__ensure_killswitch_is_running()
            self.__remove_killswitch_that_allows_specific_routes()
        else:
            self.__ensure_killswitch_is_not_running()

    def _on_error(self, **kwargs):
        if self.state == KillSwitchStateEnum.ON and (self.permanent or not self.permanent):
            self.__ensure_killswitch_is_running()
        else:
            self.__ensure_killswitch_is_not_running()

    def _on_disconnecting(self, **kwargs):
        if self.state == KillSwitchStateEnum.ON and (self.permanent or not self.permanent):
            self.__ensure_killswitch_is_running()
        else:
            self.__ensure_killswitch_is_not_running()

    def _setup_off(self):
        self.__ensure_killswitch_is_not_running()

    def _setup_killswitch(self):
        self.__ensure_killswitch_is_running()

    def __ensure_killswitch_is_not_running(self):
        self.__attempt_to_delete_killswitch_connection(self.ks_interface_name)
        self.__attempt_to_delete_killswitch_connection(self.routed_interface_name)

    def __ensure_killswitch_is_running(self):
        is_killswitch_running = False
        attempts = 3

        while attempts > 0:
            conn = self._nm_bus.get_network_manager().search_for_connection(interface_name=ks_interface_name)
            if not conn:
                self.__activate_killswitch_connection()
            else:
                is_killswitch_running = True
                break

            attempts -= 1

        if not is_killswitch_running:
            raise KillSwitchStartError(
                "Unable to start kill switch with interface {}".format(
                    self.ks_interface_name
                )
            )

    def __ensure_killswitch_only_allows_specific_routes(self, server_ip):
        self.__activate_routed_killswitch_connection(server_ip)

    def __remove_killswitch_that_allows_specific_routes(self):
        self.__attempt_to_delete_killswitch_connection(self.routed_interface_name)

    def __attempt_to_delete_killswitch_connection(self, interface_name):
        is_killswitch_running = True
        attempts = 3

        while attempts > 0:
            conn = self._nm_bus.get_network_manager().search_for_connection(interface_name=interface_name)
            if conn:
                conn.delete_connection()
            else:
                is_killswitch_running = False
                break

            attempts -= 1

        if is_killswitch_running:
            raise KillSwitchStopError("Unable to stop kill switch with interface {}".format(interface_name))

    def __activate_killswitch_connection(self):
        nmbus = NetworkManagerBus()
        nm_settings = nmbus.get_network_manager_settings()
        nm_settings.add_connection(self.__generate_killswitch_connection())

    def __generate_killswitch_connection(self):
        from proton.vpn.backend.linux.networkmanager.dbus import DbusConnection

        ks_conn = DbusConnection()
        ks_conn.settings.human_readable_id = self.ks_conn_name
        ks_conn.settings.interface_name = self.ks_interface_name

        ks_conn.ipv4.address_data = {"address": self.ipv4_dummy_addrs, "prefix": self.ipv4_dummy_suffx}
        ks_conn.ipv4.addresses = [(self.ipv4_dummy_addrs, self.ipv4_dummy_suffx, self.ipv4_dummy_gateway)]
        ks_conn.ipv4.method = "manual"
        ks_conn.ipv4.dns = ["0.0.0.0"]
        ks_conn.ipv4.dns_priority = KILLSWITCH_DNS_PRIORITY_VALUE
        ks_conn.ipv4.gateway = self.ipv4_dummy_gateway
        ks_conn.ipv4.ignore_auto_dns = True
        ks_conn.ipv4.route_metric = 98

        ks_conn.ipv6.address_data = {"address": self.ipv6_dummy_addrs, "prefix": self.ipv6_dummy_suffx}
        ks_conn.ipv6.addresses = [(self.ipv6_dummy_addrs, self.ipv6_dummy_suffx, self.ipv6_dummy_gateway)]
        ks_conn.ipv6.method = "manual"
        ks_conn.ipv6.dns = ["::1"]
        ks_conn.ipv6.dns_priority = KILLSWITCH_DNS_PRIORITY_VALUE
        ks_conn.ipv6.gateway = self.ipv6_dummy_gateway
        ks_conn.ipv6.ignore_auto_dns = True
        ks_conn.ipv6.route_metric = 98

        return ks_conn.generate_configuration()

    def __activate_routed_killswitch_connection(self, server_ip):
        nmbus = NetworkManagerBus()
        nm_settings = nmbus.get_network_manager_settings()
        nm_settings.add_connection(self.__generate_routed_killswitch_connection(server_ip))

    def __generate_routed_killswitch_connection(self, server_ip):
        import ipaddress
        subnet_list = list(
            ipaddress.ip_network(
                '0.0.0.0/0'
            ).address_exclude(ipaddress.ip_network(server_ip))
        )
        formatted_data = [
                (
                    route.split("/")[0],
                    int(route.split("/")[1]),
                    route.split("/")[0]
                ) for route in [str(ipv4) for ipv4 in subnet_list]
            ]
        from proton.vpn.backend.linux.networkmanager.dbus import DbusConnection

        ks_conn = DbusConnection()
        ks_conn.settings.human_readable_id = self.routed_conn_name
        ks_conn.settings.interface_name = self.routed_interface_name
        ks_conn.ipv4.addresses = formatted_data
        ks_conn.ipv4.method = "manual"
        ks_conn.ipv4.dns = ["0.0.0.0"]
        ks_conn.ipv4.dns_priority = KILLSWITCH_DNS_PRIORITY_VALUE
        ks_conn.ipv4.gateway = self.ipv4_dummy_gateway
        ks_conn.ipv4.ignore_auto_dns = True
        ks_conn.ipv4.route_metric = 98

        ks_conn.ipv6.address_data = {"address": self.ipv6_dummy_addrs, "prefix": self.ipv6_dummy_suffx}
        ks_conn.ipv6.addresses = [(self.ipv6_dummy_addrs, self.ipv6_dummy_suffx, self.ipv6_dummy_gateway)]
        ks_conn.ipv6.method = "manual"
        ks_conn.ipv6.dns = ["::1"]
        ks_conn.ipv6.dns_priority = KILLSWITCH_DNS_PRIORITY_VALUE
        ks_conn.ipv6.gateway = self.ipv6_dummy_gateway
        ks_conn.ipv6.ignore_auto_dns = True
        ks_conn.ipv6.route_metric = 98

        return ks_conn.generate_configuration()

    @property
    def _nm_bus(self):
        try:
            self.__nm_bus
        except AttributeError:
            self.__nm_bus = NetworkManagerBus()

        return self.__nm_bus

    @staticmethod
    def ipv4_to_int(ipv4_addr):
        import ipaddress
        return int.from_bytes(ipaddress.ip_address(ipv4_addr).packed, 'big')

    @staticmethod
    def ipv6_to_byte_list(ipv6_addr):
        import ipaddress

        import dbus
        return [
            dbus.Byte(n) for n in list(ipaddress.ip_address(ipv6_addr).packed)
        ]

    @classmethod
    def _get_priority(cls) -> int:
        return 100

    @classmethod
    def _validate(cls):
        return True
