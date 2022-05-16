from proton.vpn.backend.linux.networkmanager.dbus import (DbusConnection,
                                                          NetworkManagerBus)
from proton.vpn.killswitch.exceptions import (KillSwitchStartError,
                                              KillSwitchStopError)
import dbus.exceptions


class KillSwitchConfig:
    """This kill switch connection will block all connections to the outside
    based on a provided server IP list, passed to IPv4_addresses."""
    human_readable_id = "pvpn-routed-killswitch"
    interface_name = "pvpnroutintrf0"

    ipv4_addresses = [("100.85.0.1", 24, "100.85.0.1")]
    ipv4_method = "manual"
    ipv4_dns = ["0.0.0.0"]
    ipv4_gateway = "100.85.0.1"
    ipv4_ignore_auto_dns = True

    ipv6_address_data = {"address": "fdeb:446c:912d:08da::", "prefix": 64}
    ipv6_addresses = [("fdeb:446c:912d:08da::", 64, "fdeb:446c:912d:08da::1")]
    ipv6_method = "manual"
    ipv6_dns = ["::1"]
    ipv6_gateway = "fdeb:446c:912d:08da::1"
    ipv6_ignore_auto_dns = True

    def __init__(self, server_ip=None):
        self.__ks_conn = DbusConnection()
        if server_ip:
            self.__ks_conn.ipv4_addresses = self.__format_subnet_list(
                self.__generate_subnet_list(server_ip)
            )

    def generate_connection_config(self):
        """Non modifieable dbus connection object.

        Modifying the object that is returned here will not take
        effect.

        For changes to take effect, class proprties have to be changed.
        """
        self.__update_connection_settings()
        return self.__ks_conn.generate_configuration()

    def __update_connection_settings(self):
        self.__ks_conn.settings.human_readable_id = self.human_readable_id
        self.__ks_conn.settings.interface_name = self.interface_name

        self.__ks_conn.ipv4.address_data = self.ipv4_address_data
        self.__ks_conn.ipv4.addresses = self.ipv4_addresses
        self.__ks_conn.ipv4.method = self.ipv4_method
        self.__ks_conn.ipv4.dns = self.ipv4_dns
        self.__ks_conn.ipv4.dns_priority = self.ipv4_dns_priority
        self.__ks_conn.ipv4.gateway = self.ipv4_gateway
        self.__ks_conn.ipv4.ignore_auto_dns = self.ipv4_ignore_auto_dns
        self.__ks_conn.ipv4.route_metric = self.ipv4_route_metric

        self.__ks_conn.ipv6.address_data = self.ipv6_address_data
        self.__ks_conn.ipv6.addresses = self.ipv6_addresses
        self.__ks_conn.ipv6.method = self.ipv6_method
        self.__ks_conn.ipv6.dns = self.ipv6_dns
        self.__ks_conn.ipv6.dns_priority = self.ipv6_dns_priority
        self.__ks_conn.ipv6.gateway = self.ipv6_gateway
        self.__ks_conn.ipv6.ignore_auto_dns = self.ipv6_ignore_auto_dns
        self.__ks_conn.ipv6.route_metric = self.ipv6_route_metric

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

    def __generate_subnet_list(self, server_ip):
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


class KillSwitchConnectionHandler:
    """Kill switch connection management."""
    def add(self, killswitch_config: KillSwitchConfig):
        conn = self.is_killswitch_connection_active(killswitch_config.interface_name)

        try:
            if conn:
                conn.update_settings(killswitch_config.generate_connection_config())
        except dbus.exceptions.DBusException as e:
            raise KillSwitchStartError(
                "Unable to start kill switch with interface {}. Check NetworkManager syslogs".format(
                    killswitch_config.interface_name
                )
            ) from e

        nm_settings = NetworkManagerBus().get_network_manager_settings()
        nm_conn = None
        try:
            nm_conn = nm_settings.add_connection(killswitch_config.generate_connection_config())
        except dbus.exceptions.DBusException as e:
            raise KillSwitchStartError(
                "Unable to start kill switch with interface {}. Check NetworkManager syslogs".format(
                    killswitch_config.interface_name
                )
            ) from e

        if not nm_conn:
            raise KillSwitchStartError(
                "Unable to start kill switch with interface {}. Check NetworkManager syslogs".format(
                    killswitch_config.interface_name
                )
            )

    def remove(self, interface_name):
        conn = self.is_killswitch_connection_active(interface_name)
        if not conn:
            return

        try:
            conn.delete_connection()
        except dbus.exceptions.DBusException as e:
            raise KillSwitchStopError(
                "Unable to stop kill switch with interface {}. Check NetworkManager syslogs".format(
                    interface_name
                )
            ) from e

        if self.is_killswitch_connection_active(interface_name):
            raise KillSwitchStopError(
                "Unable to stop kill switch with interface {}. Check NetworkManager syslogs".format(
                    interface_name
                )
            )

    def is_killswitch_connection_active(self, interface_name) -> "ConnectionSettingsAdapter":
        conn = NetworkManagerBus().get_network_manager().search_for_connection(interface_name=interface_name)
        return conn if conn else None
