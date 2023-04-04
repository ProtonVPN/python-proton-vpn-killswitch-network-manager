"""
Init module that makes the NetworkManager Kill Switch class to be easily importable.
"""
from proton.vpn.killswitch.backend.linux.networkmanager.nmkillswitch import NMKillSwitch

__all__ = ["NMKillSwitch"]
