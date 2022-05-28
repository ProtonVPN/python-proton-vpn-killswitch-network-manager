import os

import pytest
from proton.vpn.killswitch.backend.linux.networkmanager.killswitch_connection import (
    KillSwitchConfig, KillSwitchConnectionHandler)
from proton.vpn.killswitch.interface.exceptions import KillSwitchException
import subprocess


TEST_HUMAN_READEABLE_ID = "test-pvpn-killswitch"
TEST_INTERFACE_NAME = "testpvpn0"


def _assert_connection_exist():
    output = int(os.system(f"nmcli -g GENERAL.STATE c s \"{TEST_HUMAN_READEABLE_ID}\""))
    assert output == 0


def _assert_connection_does_not_exist():
    output = int(os.system(f"nmcli -g GENERAL.STATE c s \"{TEST_HUMAN_READEABLE_ID}\""))
    assert output != 0


def _nmcli_del_connection():
    os.system(f"nmcli c del {TEST_HUMAN_READEABLE_ID}")


class TestIntegrationKillSwitchConnectionHandler:
    def setup_class(cls):
        _nmcli_del_connection()
        _assert_connection_does_not_exist()

    def teardown_class(cls):
        _nmcli_del_connection()
        _assert_connection_does_not_exist()

    @pytest.fixture
    def cleanup_env(self):
        yield {}
        _nmcli_del_connection()
        _assert_connection_does_not_exist()

    @pytest.fixture
    def test_killswitch_config(self):
        cfg = KillSwitchConfig()
        cfg.human_readable_id = TEST_HUMAN_READEABLE_ID
        cfg.interface_name = TEST_INTERFACE_NAME
        yield cfg

    def _nmcli_add_connection(self):
        os.system(f"nmcli c a type dummy ifname {TEST_INTERFACE_NAME} con-name {TEST_HUMAN_READEABLE_ID}")

    def _assert_killswithch_connection_was_updated(self, ks_config):
        nmcli_string = f"nmcli -g ipv4.addresses c s {TEST_HUMAN_READEABLE_ID}"
        ipv4_addresses = subprocess.check_output(nmcli_string.split(" ")).decode().strip("\n").split(",")
        ipv4_addresses = tuple([addr.replace(" ", "") for addr in ipv4_addresses])
        assert ipv4_addresses != tuple(["{}/{}".format(_dict["address"], _dict["prefix"]) for _dict in ks_config.ipv4_address_data])

    @pytest.mark.parametrize("arg", [None, KillSwitchConfig()])
    def test_init_expected_args(self, arg):
        KillSwitchConnectionHandler(arg)

    @pytest.mark.parametrize("arg", [False, "TestString"])
    def test_init_with_raises_exception(self, arg):
        with pytest.raises(TypeError):
            KillSwitchConnectionHandler(arg)

    def test_add_and_remove_connection(self, cleanup_env, test_killswitch_config):
        handler = KillSwitchConnectionHandler(test_killswitch_config)
        handler.add()
        _assert_connection_exist()
        handler.remove()
        _assert_connection_does_not_exist()

    def test_update_connection(self, cleanup_env, test_killswitch_config):
        handler = KillSwitchConnectionHandler(test_killswitch_config)
        handler.add()
        _assert_connection_exist()
        handler.update("192.168.1.1")
        self._assert_killswithch_connection_was_updated(test_killswitch_config)

    def test_add_connection_and_connection_exists_raises_exception(self, cleanup_env, test_killswitch_config):
        self._nmcli_add_connection()
        handler = KillSwitchConnectionHandler(test_killswitch_config)
        with pytest.raises(KillSwitchException):
            handler.add()

    def test_update_connection_and_connection_does_not_exist_raises_exception(self, cleanup_env, test_killswitch_config):
        handler = KillSwitchConnectionHandler(test_killswitch_config)
        with pytest.raises(KillSwitchException):
            handler.update("192.149.1.1")

    def test_remove_connection_and_connection_does_not_exist_raises_exception(self, cleanup_env, test_killswitch_config):
        handler = KillSwitchConnectionHandler(test_killswitch_config)
        with pytest.raises(KillSwitchException):
            handler.remove()
