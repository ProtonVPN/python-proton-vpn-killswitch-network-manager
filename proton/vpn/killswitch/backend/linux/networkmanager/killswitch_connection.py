from proton.vpn.backend.linux.networkmanager.dbus import DbusConnection, NetworkManagerBus


class BaseKillSwitchConnectionType:
    """Base class for easy kill switch connection management."""
    human_readable_id = None
    interface_name = None

    ipv4_address_data = None
    ipv4_addresses = None
    ipv4_method = None
    ipv4_dns = None
    ipv4_dns_priority = -1500
    ipv4_gateway = None
    ipv4_ignore_auto_dns = None
    ipv4_route_metric = 98

    ipv6_address_data = None
    ipv6_addresses = None
    ipv6_method = None
    ipv6_dns = None
    ipv6_dns_priority = -1500
    ipv6_gateway = None
    ipv6_ignore_auto_dns = None
    ipv6_route_metric = 98

    def __init__(self):
        self.__ks_conn = DbusConnection()
        self.__nmbus = NetworkManagerBus()

    def add(self):
        if self.is_killswitch_connection_active:
            return True

        nm_settings = self.__nmbus.get_network_manager_settings()

        if not nm_settings.add_connection(self.__generate_connection_config()):
            return False

        return True

    def remove(self):
        conn = self.is_killswitch_connection_active
        if not conn:
            return True

        conn.delete_connection()

        if self.is_killswitch_connection_active:
            return False

        return True

    @property
    def is_killswitch_connection_active(self) -> "ConnectionSettingsAdapter":
        conn = self.__nmbus.get_network_manager().search_for_connection(interface_name=self.interface_name)
        return conn if conn else None

    def __generate_connection_config(self):
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


class FullKillSwitch(BaseKillSwitchConnectionType):
    """This kill switch connection will block all connections
    to the outside."""
    human_readable_id = "pvpn-killswitch"
    interface_name = "pvpnksintrf0"

    ipv4_address_data = {"address": "100.85.0.1", "prefix": 24}
    ipv4_addresses = [("100.85.0.1", 24, "100.85.0.1")]
    ipv4_method = "manual"
    ipv4_dns = ["0.0.0.0"]
    ipv4_dns_priority = -1500
    ipv4_gateway = "100.85.0.1"
    ipv4_ignore_auto_dns = True
    ipv4_route_metric = 98

    ipv6_address_data = {"address": "fdeb:446c:912d:08da::", "prefix": 64}
    ipv6_addresses = [("fdeb:446c:912d:08da::", 64, "fdeb:446c:912d:08da::1")]
    ipv6_method = "manual"
    ipv6_dns = ["::1"]
    ipv6_dns_priority = -1500
    ipv6_gateway = "fdeb:446c:912d:08da::1"
    ipv6_ignore_auto_dns = True
    ipv6_route_metric = 98


class RoutedKillSwitch(BaseKillSwitchConnectionType):
    """This kill switch connection will block all connections to the outside
    based on a provided server IP list, passed to IPv4_addresses."""
    human_readable_id = "pvpn-routed-killswitch"
    interface_name = "pvpnroutintrf0"
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
