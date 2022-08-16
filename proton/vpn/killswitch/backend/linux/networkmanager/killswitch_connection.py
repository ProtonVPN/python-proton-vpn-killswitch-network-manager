import ipaddress
import logging
import operator

from dbus_network_manager import DbusConnection, NetworkManagerBus
from dbus_network_manager.exceptions import ProtonDbusException
from proton.vpn.killswitch.interface.exceptions import KillSwitchException

logger = logging.getLogger(__name__)


class KillSwitchConfig:
    """
    Further abstracts the creation of a kill switch dummy connection for network manager.

    The dbus kill switch connection is created internally. Class properties expose what can be
    changed although, for the most part nothing should be changed, except
    when creating a route for a specific server ip.
    """
    human_readable_id = "pvpn-killswitch"
    interface_name = "pvpnksintrf0"

    ipv4_address_data = [{"address": "100.85.0.1", "prefix": 24}]
    ipv4_addresses = [("100.85.0.1", 24, "100.85.0.1")]
    ipv4_method = "manual"
    ipv4_dns = ["0.0.0.0"]
    ipv4_dns_priority = -1500
    ipv4_gateway = "100.85.0.1"
    ipv4_ignore_auto_dns = True
    ipv4_route_metric = 98

    ipv6_address_data = [{"address": "fdeb:446c:912d:08da::", "prefix": 64}]
    ipv6_addresses = [("fdeb:446c:912d:08da::", 64, "fdeb:446c:912d:08da::1")]
    ipv6_method = "manual"
    ipv6_dns = ["::1"]
    ipv6_dns_priority = -1500
    ipv6_gateway = "fdeb:446c:912d:08da::1"
    ipv6_ignore_auto_dns = True
    ipv6_route_metric = 98

    def __init__(self, server_ip=None):
        self.__ks_conn = DbusConnection()
        if server_ip:
            self.update_ipv4_addresses(server_ip)

    def update_ipv4_addresses(self, server_ip: str):
        """
            :param server_ip: ipv4 address
            :type server_ip: str

        Internally updates the ipv4 addresses so that all routes are
        blocked with the exception of the `server_ip` that was provided.
        This usually helps if the user is running a permanent kill switch
        (which block all traffic) by creating a small gap so that only
        the `server_ip` can reach outside while rest of the traffic is blocked.
        """
        try:
            ipaddress.ip_network(server_ip)
        except ValueError as e:
            raise ValueError(f"{e}") from e

        self.ipv4_addresses = self.__format_subnet_list(
            self.__generate_subnet_list(server_ip)
        )

    def generate_connection_config(self) -> "dbus.Dictionary":  # noqa: F821
        """
            :return: connection configurations in dict format
            :rtype: dbus.Dictionary

        Properly updates the configuration of the kill switch connection
        and generates it in a proper format so that it can be added easily.
        """
        self.__update_connection_settings()
        return self.__ks_conn.generate_configuration()

    def __update_connection_settings(self):
        """
        This method configures the kill switch internally at once. It is private
        because this is called internally when calling `generate_connection_config()`.

        Should not be called by itself.
        """
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

    def __format_subnet_list(self, subnet_list: list) -> list:
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

    def __generate_subnet_list(self, server_ip: str) -> list:
        """
            :param server_ip: vpn server ip
            :type server_ip: str
            :return: list with ip that should be included
            :rtype: list(str)
        """
        return list(
            ipaddress.ip_network(
                '0.0.0.0/0'
            ).address_exclude(ipaddress.ip_network(server_ip))
        )


class KillSwitchConnectionHandler:
    """Kill switch connection management."""

    def __init__(self, killswitch_config: KillSwitchConfig = None):
        if killswitch_config is not None and not isinstance(killswitch_config, KillSwitchConfig):
            raise TypeError(
                "Wrong type for 'killswitch_config' argument. "
                f"Expected {type(None)} or {KillSwitchConfig} "
                f"but got {type(killswitch_config)}"
            )
        self.__killswitch_config = killswitch_config or KillSwitchConfig()

    def add(self):
        if self.is_killswitch_connection_active():
            raise KillSwitchException(
                f"Kill switch connection "
                f"{self.__killswitch_config.interface_name} already exists."
            )

        nm_settings = NetworkManagerBus().get_network_manager_settings()
        try:
            nm_settings.add_connection(self.__killswitch_config.generate_connection_config())
        except ProtonDbusException as e:
            raise KillSwitchException(
                f"Unable to start kill switch with interface "
                f"{self.__killswitch_config.interface_name}. "
                f"{e}"
            ) from e

    def remove(self):
        if not self.is_killswitch_connection_active():
            raise KillSwitchException(
                f"Kill switch connection {KillSwitchConfig.interface_name} "
                f"could not be found."
            )

        try:
            self._get_connection().delete_connection()
        except ProtonDbusException as e:
            raise KillSwitchException(
                f"Unable to stop kill switch with interface "
                f"{self.__killswitch_config.interface_name}."
            ) from e

    def update(self, server_ip: str):
        if not self.is_killswitch_connection_active():
            raise KillSwitchException(
                f"Kill switch connection {KillSwitchConfig.interface_name} "
                f"could not be found."
            )

        self.__killswitch_config.update_ipv4_addresses(server_ip)

        try:
            self._get_connection().update_settings(self.__killswitch_config.generate_connection_config())
        except ProtonDbusException as e:
            raise KillSwitchException(
                f"An error occured while trying to update connection "
                f"{self.__killswitch_config.interface_name}."
            ) from e

    def is_killswitch_connection_active(self):
        return operator.truth(self._get_connection())

    def _get_connection(self):
        return NetworkManagerBus().get_network_manager().search_for_connection(
            interface_name=self.__killswitch_config.interface_name
        )
