import os

import pytest
import requests
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    KillSwitchConfig, KillSwitchConnectionHandler, NetworkManagerBus)


class TestKillSwitchConfig:
    def setup_class(cls):
        os.system(f"nmcli c del {KillSwitchConfig.human_readable_id}")
        assert not NetworkManagerBus().get_network_manager().search_for_connection(
            interface_name=KillSwitchConfig.human_readable_id
        )

    def teardown_class(cls):
        os.system(f"nmcli c del {KillSwitchConfig.human_readable_id}")
        assert not NetworkManagerBus().get_network_manager().search_for_connection(
            interface_name=KillSwitchConfig.human_readable_id
        )

    @pytest.mark.parametrize("arg", [None, "192.168.1.1"])
    def test_init_expected_args(self, arg):
        KillSwitchConfig(arg)

    @pytest.mark.parametrize("arg", ["0.0", "192.168.", "19-1.231.32.1"])
    def test_init_raises_exception(self, arg):
        with pytest.raises(ValueError):
            KillSwitchConfig(arg)

    def test_activate_non_routed_connection(self):
        nm_settings = NetworkManagerBus().get_network_manager_settings()
        cfg = KillSwitchConfig()

        nm_settings.add_connection(cfg.generate_connection_config())
        assert NetworkManagerBus().get_network_manager().search_for_connection(
            interface_name=cfg.interface_name
        )
        with pytest.raises(requests.exceptions.ConnectionError):
            self._test_network_connection()

    def test_activate_routed_connection(self):
        nm_settings = NetworkManagerBus().get_network_manager_settings()
        cfg = KillSwitchConfig("192.140.1.1")

        nm_settings.add_connection(cfg.generate_connection_config())
        assert NetworkManagerBus().get_network_manager().search_for_connection(
            interface_name=cfg.interface_name
        )
        # FIX-ME: ideally we should have and IP which we could test if we can
        # reach it or not
        with pytest.raises(requests.exceptions.ConnectionError):
            self._test_network_connection()

    def _test_network_connection(self):
        requests.get("https://ip.me", timeout=(1, 1))


class TestKillSwitchConnectionHandler:
    def setup_class(cls):
        os.system(f"nmcli c del {KillSwitchConfig.human_readable_id}")
        assert not NetworkManagerBus().get_network_manager().search_for_connection(
            interface_name=KillSwitchConfig.human_readable_id
        )

    def teardown_class(cls):
        os.system(f"nmcli c del {KillSwitchConfig.human_readable_id}")
        assert not NetworkManagerBus().get_network_manager().search_for_connection(
            interface_name=KillSwitchConfig.human_readable_id
        )

    @pytest.mark.parametrize("arg", [None, KillSwitchConfig()])
    def test_init_expected_args(self, arg):
        KillSwitchConnectionHandler(arg)

    @pytest.mark.parametrize("arg", [False, "TestString"])
    def test_init_with_raises_exception(self, arg):
        with pytest.raises(TypeError):
            KillSwitchConnectionHandler(arg)

    def test_add_connection(self):
        handler = KillSwitchConnectionHandler(KillSwitchConfig())
        handler.add()
        assert handler.is_killswitch_connection_active()
        os.system(f"nmcli c del {KillSwitchConfig.human_readable_id}")
        assert not handler.is_killswitch_connection_active()

    def test_update_connection(self):
        handler = KillSwitchConnectionHandler(KillSwitchConfig())
        handler.add()
        assert handler.is_killswitch_connection_active()
        handler.update("192.168.1.1")
        assert handler.is_killswitch_connection_active()
        os.system(f"nmcli c del {KillSwitchConfig.human_readable_id}")
        assert not handler.is_killswitch_connection_active()

    def test_remove_connection(self):
        handler = KillSwitchConnectionHandler(KillSwitchConfig())
        handler.add()
        assert handler.is_killswitch_connection_active()
        handler.remove()
        assert not handler.is_killswitch_connection_active()
