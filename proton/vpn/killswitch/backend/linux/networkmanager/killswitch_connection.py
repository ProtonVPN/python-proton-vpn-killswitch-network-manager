"""
This modules contains the classes that communicate with NetworkManager.
"""
import ipaddress
import subprocess
from proton.vpn import logging


logger = logging.getLogger(__name__)


class KillSwitchConfig:  # pylint: disable=too-few-public-methods
    """
    Further abstracts the creation of a kill switch dummy connection for network manager.

    The dbus kill switch connection is created internally. Class properties expose what can be
    changed although, for the most part nothing should be changed, except
    when creating a route for a specific server ip.
    """
    human_readable_id = "pvpn-killswitch"
    interface_name = "pvpnksintrf0"
    human_readable_id_ipv6 = "pvpn-killswitch-ipv6"
    interface_name_ipv6 = "ipv6leakintrf0"

    ipv4_addresses = ["100.85.0.1"]
    ipv4_prefix = 24
    ipv4_method = "manual"
    ipv4_dns = ["0.0.0.0"]
    ipv4_dns_priority = -1400
    ipv4_gateway = "100.85.0.1"
    ipv4_ignore_auto_dns = True
    ipv4_route_metric = 97

    ipv6_addresses = ["fdeb:446c:912d:08da::"]
    ipv6_prefix = 64
    ipv6_method = "manual"
    ipv6_dns = ["::1"]
    ipv6_dns_priority = -1400
    ipv6_gateway = "fdeb:446c:912d:08da::1"
    ipv6_ignore_auto_dns = True
    ipv6_route_metric = 97

    def create_hole_for_ipv4(self, server_ip: str):
        """
            :param server_ip: ipv4 address
            :type server_ip: str

        Internally updates the ipv4 addresses so that all routes are
        blocked with the exception of the `server_ip` that was provided.
        This usually helps if the user is running a permanent kill switch
        (which block all traffic) by creating a small gap so that only
        the `server_ip` can reach outside while rest of the traffic is blocked.
        """
        self.ipv4_addresses = self._generate_subnet_list(server_ip)

    def _generate_subnet_list(self, server_ip: str) -> list:
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
        self._killswitch_config = killswitch_config or KillSwitchConfig()

    @property
    def is_killswitch_connection_active(self) -> bool:
        """Returns if general kill switch is active or not."""
        return False

    @property
    def is_ipv6_leak_protection_connection_active(self) -> bool:
        """Returns if IPv6 kill switch is active or not."""
        subprocess_command = [
            "nmcli", "c", "s", self._killswitch_config.human_readable_id_ipv6
        ]
        completed_process = subprocess.run(subprocess_command, capture_output=True, check=False)
        return completed_process.returncode == 0

    def add(self, server_ip: str):
        """Adds general kill switch to NetworkManager"""
        raise NotImplementedError

    def remove(self):
        """Removes general kill switch from NetworkManager."""
        raise NotImplementedError

    def update(self, server_ip: str):
        """Update the general kill switch."""
        raise NotImplementedError

    def add_ipv6_leak_protection(self):
        """Adds IPv6 kill switch to NetworkManager."""
        ipv6_config = f"{self._killswitch_config.ipv6_addresses[0]}/"\
            f"{str(self._killswitch_config.ipv6_prefix)}"
        subprocess_command = [
            "nmcli", "c", "a", "type", "dummy",
            "ifname", self._killswitch_config.interface_name_ipv6,
            "con-name", self._killswitch_config.human_readable_id_ipv6,
            "ipv6.method", "manual",
            "ipv6.addresses", ipv6_config,
            "ipv6.gateway", self._killswitch_config.ipv6_gateway,
            "ipv6.route-metric", str(self._killswitch_config.ipv6_route_metric),
            "ipv6.dns-priority", str(self._killswitch_config.ipv6_dns_priority),
            "ipv6.ignore-auto-dns", "yes",
            "ipv6.dns", self._killswitch_config.ipv6_dns[0]
        ]
        proccess = subprocess.run(subprocess_command, capture_output=True, check=False)
        logger.info(proccess.stdout.decode('utf-8'), category="killswitch:ipv6", event="add")

    def remove_ipv6_leak_protection(self):
        """Removes IPv6 kill switch from NetworkManager."""
        subprocess_command = [
            "nmcli", "c", "delete",
            self._killswitch_config.human_readable_id_ipv6
        ]
        proccess = subprocess.run(subprocess_command, capture_output=True, check=False)
        logger.info(proccess.stdout.decode('utf-8'), category="killswitch:ipv6", event="remove")
