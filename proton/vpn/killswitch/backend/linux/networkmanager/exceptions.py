class KillswitchError(Exception): # noqa
    """Killswitch error."""


class CreateKillswitchError(KillswitchError):
    """Create killswitch error"""


class CreateRoutedKillswitchError(CreateKillswitchError):
    """Create routed killswitch error"""


class CreateBlockingKillswitchError(CreateKillswitchError):
    """Create routed killswitch error"""


class DeleteKillswitchError(KillswitchError):
    """Delete killswitch error."""


class ActivateKillswitchError(KillswitchError):
    """Activate killswitch error."""


class DectivateKillswitchError(KillswitchError):
    """Deactivate killswitch error."""


class AvailableConnectivityCheckError(KillswitchError):
    """Available connectivity check error."""


class DisableConnectivityCheckError(KillswitchError):
    """Disable connectivity check error."""