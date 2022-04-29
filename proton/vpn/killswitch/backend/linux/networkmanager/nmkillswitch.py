from proton.vpn.killswitch import KillSwitch

from .constants import (KILLSWITCH_CONN_NAME, KILLSWITCH_DNS_PRIORITY_VALUE,
                        KILLSWITCH_INTERFACE_NAME, ROUTED_CONN_NAME,
                        ROUTED_INTERFACE_NAME, IPv4_DUMMY_ADDRESS,
                        IPv4_DUMMY_ADDRESS_SUFFIX, IPv4_DUMMY_GATEWAY,
                        IPv6_DUMMY_ADDRESS, IPv6_DUMMY_ADDRESS_SUFFIX,
                        IPv6_DUMMY_GATEWAY)
from proton.vpn.killswitch.enums import KillSwitchStateEnum


class NMKillSwitch(KillSwitch):

    ks_conn_name = KILLSWITCH_CONN_NAME
    ks_interface_name = KILLSWITCH_INTERFACE_NAME

    routed_conn_name = ROUTED_CONN_NAME
    routed_interface_name = ROUTED_INTERFACE_NAME

    ipv4_dummy_addrs = IPv4_DUMMY_ADDRESS
    ipv4_dummy_gateway = IPv4_DUMMY_GATEWAY
    ipv6_dummy_addrs = IPv6_DUMMY_ADDRESS
    ipv6_dummy_gateway = IPv6_DUMMY_GATEWAY

    def _determine_initial_state(self):
        self.on()

    def _setup_off(self, **kwargs):
        self._disable_killswitch()

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
            self.__ensure_killswitch_only_allows_specific_routes()

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

    def __ensure_killswitch_is_not_running(self):
        pass

    def __ensure_killswitch_is_running(self):
        pass

    def __ensure_killswitch_only_allows_specific_routes(self):
        pass

    def __remove_killswitch_that_allows_specific_routes(self):
        pass

    @classmethod
    def _get_priority(cls) -> int:
        return 100

    @classmethod
    def _validate(cls):
        return True

    @staticmethod
    def ipv4_to_int(ipv4_addr):
        import ipaddress
        return int.from_bytes(ipaddress.ip_address(ipv4_addr).packed, 'big')

    @staticmethod
    def ipv6_to_byte_list(ipv6_addr):
        import dbus
        import ipaddress
        return [
            dbus.Byte(n) for n in list(ipaddress.ip_address(ipv6_addr).packed)
        ]

    def __activate_killswitch_connection(self):
        from proton.vpn.backend.linux.networkmanager.dbus import \
            NetworkManagerBus
        nmbus = NetworkManagerBus()
        nm_settings = nmbus.get_network_manager_settings()
        try:
            nm_settings.add_connection(self.__generate_killswitch_connection())
        except: # noqa
            return False

        return True

    def __generate_killswitch_connection(self):
        import uuid
        import dbus

        settings_connection = dbus.Dictionary({
                    'type': 'dummy',
                    'uuid': str(uuid.uuid1()),
                    'id': KILLSWITCH_CONN_NAME,
                    'interface-name': KILLSWITCH_INTERFACE_NAME})

        addr_ipv4 = dbus.Dictionary({
            'address': IPv4_DUMMY_ADDRESS,
            'prefix': IPv4_DUMMY_ADDRESS_SUFFIX,
        })

        ipv4_addresses = dbus.Array(
            [
                NMKillSwitch.ipv4_to_int(IPv4_DUMMY_ADDRESS),
                dbus.UInt32(IPv4_DUMMY_ADDRESS_SUFFIX),
                NMKillSwitch.ipv4_to_int(IPv4_DUMMY_GATEWAY)
            ], signature=dbus.Signature('u')
        )
        settings_ipv4 = dbus.Dictionary({
            'address-data': dbus.Array([addr_ipv4], signature=dbus.Signature('a{sv}')),
            'method': 'manual',
            'dns-priority': KILLSWITCH_DNS_PRIORITY_VALUE,
            'gateway': IPv4_DUMMY_GATEWAY,
            'ignore-auto-dns': True,
            'route-metric': 98,
            'addresses': dbus.Array([ipv4_addresses], signature=dbus.Signature('au')),
            'dns': dbus.Array(
                [
                    NMKillSwitch.ipv4_to_int("0.0.0.0")
                ], signature=dbus.Signature('u')
            ),
        })

        addr_ipv6 = dbus.Dictionary({
            'address': IPv6_DUMMY_ADDRESS,
            'prefix': IPv6_DUMMY_ADDRESS_SUFFIX,
        })
        addresses_ipv6 = dbus.Struct(
            (
                NMKillSwitch.ipv6_to_byte_list(IPv6_DUMMY_ADDRESS),
                dbus.UInt32(IPv6_DUMMY_ADDRESS_SUFFIX),
                NMKillSwitch.ipv6_to_byte_list(IPv6_DUMMY_GATEWAY)
            )
        )
        settings_ipv6 = dbus.Dictionary({
            'address-data': dbus.Array([addr_ipv6], signature=dbus.Signature('a{sv}')),
            'method': 'manual',
            'dns-priority': KILLSWITCH_DNS_PRIORITY_VALUE,
            'gateway': IPv6_DUMMY_GATEWAY,
            'ignore-auto-dns': True,
            'route-metric': 98,
            'addresses': dbus.Array([addresses_ipv6]),
            'dns': dbus.Array(
                [
                    dbus.Array(
                        NMKillSwitch.ipv6_to_byte_list("::1"), signature=dbus.Signature('y')
                    )
                ], signature=dbus.Signature("ay")
            )
        })

        con = dbus.Dictionary({
            'connection': settings_connection,
            'ipv4': settings_ipv4,
            'ipv6': settings_ipv6
        })

        return con
