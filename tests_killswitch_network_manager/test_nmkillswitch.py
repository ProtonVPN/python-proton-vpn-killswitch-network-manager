from proton.vpn.killswitch.backend.linux.networkmanager import NMKillSwitch
from proton.vpn.killswitch.interface.enums import KillSwitchStateEnum
from unittest.mock import Mock


def test_get_priority():
    assert NMKillSwitch._get_priority()


def test_get_validate():
    assert NMKillSwitch._validate()


def test_enable():
    ks_handler = Mock()
    ks_handler.is_killswitch_connection_active.return_value = False
    ks = NMKillSwitch(KillSwitchStateEnum.OFF, ks_handler)
    ks_handler.is_killswitch_connection_active.return_value = True
    # Given that _enable adds a kill switch connection, there should be no connection
    # before the add() method. After executing the add() method, the kill switch
    # connection should be active.
    ks_handler.is_killswitch_connection_active.side_effect = [False, True]
    ks._enable()
    assert ks_handler.add.called


def test_disable():
    ks_handler = Mock()
    ks_handler.is_killswitch_connection_active.return_value = False
    ks = NMKillSwitch(KillSwitchStateEnum.OFF, ks_handler)
    ks_handler.is_killswitch_connection_active.return_value = True
    # Given that _enable adds a kill switch connection, there should be no connection
    # before the add() method. After executing the add() method, the kill switch
    # connection should be active.
    ks_handler.is_killswitch_connection_active.side_effect = [False, True]
    ks._enable()
    assert ks_handler.add.called


def test_update():
    ks_handler = Mock()
    ks_handler.is_killswitch_connection_active.return_value = False
    ks = NMKillSwitch(KillSwitchStateEnum.OFF, ks_handler)
    ks_handler.is_killswitch_connection_active.return_value = True
    # Given that _enable adds a kill switch connection, there should be no connection
    # before the add() method. After executing the add() method, the kill switch
    # connection should be active.
    ks_handler.is_killswitch_connection_active.side_effect = [True]
    ks._update()
    assert ks_handler.update.called
