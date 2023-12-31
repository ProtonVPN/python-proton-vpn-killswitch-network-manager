"""
Wrapper over the NetworkManager client.


Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
from concurrent.futures import Future
from threading import Thread, Lock
from typing import Callable, Optional

from gi.repository import NM, GLib, Gio


from proton.vpn import logging
from proton.vpn.killswitch.interface.exceptions import KillSwitchException

logger = logging.getLogger(__name__)


class NMClient:
    """
    Wrapper over the NetworkManager client.
    It also starts the GLib main loop used by the NetworkManager client.
    """
    _lock = Lock()
    _main_context = None
    _nm_client = None

    @classmethod
    def initialize_nm_client_singleton(cls):
        """
        Initializes the NetworkManager client singleton.

        If the singleton was initialized, this method will do nothing. However,
        if the singleton wasn't initialized it will initialize it, starting
        a new GLib MainLoop.

        A double-checked lock is used to avoid the possibility of multiple
        threads concurrently creating multiple instances of the NM client
        (with their own main loops).
        """
        if cls._nm_client:
            return

        with cls._lock:
            if not cls._nm_client:
                cls._initialize_nm_client_singleton()

    @classmethod
    def _initialize_nm_client_singleton(cls):
        cls._main_context = GLib.MainContext()
        cls._nm_client = NM.Client()
        # Setting daemon=True when creating the thread makes that this thread
        # exits abruptly when the python process exits. It would be better to
        # exit the thread running the main loop calling self._main_loop.quit().
        Thread(target=cls._run_main_loop, daemon=True).start()

        callback, future = cls.create_nmcli_callback(
            finish_method_name="new_finish"
        )

        def new_async():
            cls._assert_running_on_main_loop_thread()
            cls._nm_client.new_async(cancellable=None, callback=callback, user_data=None)

        cls._run_on_main_loop_thread(new_async)
        cls._nm_client = future.result()

    @classmethod
    def _run_main_loop(cls):
        main_loop = GLib.MainLoop(cls._main_context)
        cls._main_context.push_thread_default()
        main_loop.run()

    @classmethod
    def _assert_running_on_main_loop_thread(cls):
        """
        This method asserts that the thread running it is the one iterating
        GLib's main loop.

        It's useful to call this method at the beginning of any code block
        that's supposed to run in GLib's main loop, to avoid hard-to-debug
        issues.

        For more info:
        https://developer.gnome.org/documentation/tutorials/main-contexts.html#checking-threading
        """
        assert cls._main_context.is_owner()

    @classmethod
    def _run_on_main_loop_thread(cls, function):
        cls._main_context.invoke_full(priority=GLib.PRIORITY_DEFAULT, function=function)

    @classmethod
    def create_nmcli_callback(cls, finish_method_name: str) -> (Callable, Future):
        """Creates a callback for the NM client finish method and a Future that will
        resolve once the callback is called."""
        future = Future()
        future.set_running_or_notify_cancel()

        def callback(source_object, res, userdata):  # pylint: disable=unused-argument
            cls._assert_running_on_main_loop_thread()
            try:
                # On errors, according to the docs, the callback can be called
                # with source_object/res set to None.
                # https://lazka.github.io/pgi-docs/index.html#NM-1.0/classes/Client.html#NM.Client.new_async
                if not source_object or not res:

                    raise KillSwitchException(
                        f"An unexpected error occurred initializing NMClient: "
                        f"source_object = {source_object}, res = {res}."
                    )

                result = getattr(source_object, finish_method_name)(res)

                # According to the docs, None is returned on errors
                # https://lazka.github.io/pgi-docs/index.html#NM-1.0/classes/Client.html#NM.Client.new_finish
                if not result:
                    raise KillSwitchException(
                        "An unexpected error occurred initializing NMClient"
                    )

                future.set_result(result)
            except BaseException as exc:  # pylint: disable=broad-except
                future.set_exception(exc)

        return callback, future

    def __init__(self):
        self.initialize_nm_client_singleton()

    def add_connection_async(
        self, connection: NM.Connection, save_to_disk: bool = False
    ) -> Future:
        """
        Adds a new connection asynchronously.
        https://lazka.github.io/pgi-docs/#NM-1.0/classes/Client.html#NM.Client.add_connection_async
        :param connection: connection to be added.
        :return: a Future to keep track of completion.
        """
        callback, future = self.create_nmcli_callback(
            finish_method_name="add_connection_finish"
        )

        def add_connection_async():
            self._assert_running_on_main_loop_thread()
            self._nm_client.add_connection_async(
                connection=connection,
                save_to_disk=save_to_disk,
                cancellable=None,
                callback=callback,
                user_data=None
            )

        self._run_on_main_loop_thread(add_connection_async)
        return future

    def remove_connection_async(
            self, connection: NM.RemoteConnection
    ) -> Future:
        """
        Removes the specified connection asynchronously.
        https://lazka.github.io/pgi-docs/#NM-1.0/classes/RemoteConnection.html#NM.RemoteConnection.delete_async
        :param connection: connection to be removed.
        :return: a Future to keep track of completion.
        """
        callback, future = self.create_nmcli_callback(
            finish_method_name="delete_finish"
        )

        def delete_async():
            self._assert_running_on_main_loop_thread()
            connection.delete_async(
                None,
                callback,
                None
            )

        self._run_on_main_loop_thread(delete_async)
        return future

    def get_active_connection(self, conn_id: str) -> Optional[NM.ActiveConnection]:
        """
        Returns the specified active connection, if existing.
        :param conn_id: ID of the active connection.
        :return: the active connection if it was found. Otherwise, None.
        """
        active_connections = self._nm_client.get_active_connections()

        for connection in active_connections:
            if connection.get_id() == conn_id:
                return connection

        return None

    def get_connection(self, conn_id: str) -> Optional[NM.RemoteConnection]:
        """
        Returns the specified connection, if existing.
        :param conn_id: ID of the connection.
        :return: the connection if it was found. Otherwise, None.
        """
        return self._nm_client.get_connection_by_id(conn_id)

    def get_nm_running(self) -> bool:
        """Returns if NetworkManager daemon is running or not."""
        return self._nm_client.get_nm_running()

    def connectivity_check_get_enabled(self) -> bool:
        """Returns if connectivity check is enabled or not."""
        return self._nm_client.connectivity_check_get_enabled()

    def disable_connectivity_check(self) -> Future:
        """Since `connectivity_check_set_enabled` has been deprecated,
        we have to resort to lower lever commands.
        https://lazka.github.io/pgi-docs/#NM-1.0/classes/Client.html#NM.Client.connectivity_check_set_enabled

        This change is necessary since if this feature is enabled,
        dummy connection are inflated with a value of 20000.

        https://developer-old.gnome.org/NetworkManager/stable/NetworkManager.conf.html
        (see under `connectivity section`)
        """
        return self._dbus_set_property(
            object_path="/org/freedesktop/NetworkManager",
            interface_name="org.freedesktop.NetworkManager",
            property_name="ConnectivityCheckEnabled",
            value=GLib.Variant("b", False),
            timeout_msec=-1,
            cancellable=None
        )

    def _dbus_set_property(
            self, *userdata, object_path: str, interface_name: str, property_name: str,
            value: GLib.Variant, timeout_msec: int = -1,
            cancellable: Gio.Cancellable = None,
    ) -> Future:  # pylint: disable=too-many-arguments
        """Set NM properties since dedicated methods have been deprecated deprecated.
        Source: https://lazka.github.io/pgi-docs/#NM-1.0/classes/Client.html"""  # noqa

        callback, future = self.create_nmcli_callback(
            finish_method_name="dbus_set_property_finish"
        )

        def set_property_async():
            self._assert_running_on_main_loop_thread()
            self._nm_client.dbus_set_property(
                object_path, interface_name, property_name,
                value, timeout_msec, cancellable, callback,
                userdata
            )

        self._run_on_main_loop_thread(set_property_async)
        return future
