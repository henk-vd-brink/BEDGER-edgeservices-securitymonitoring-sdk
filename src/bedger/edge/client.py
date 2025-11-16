from __future__ import annotations

import copy
import json
import socket
import jsonpatch
import logging
from http.client import HTTPConnection
from typing import Any

from .config import Config
from .entities.device_event import DeviceEvent
from . import entities
from .errors import (
    ConnectionError,
    SendError,
    HTTPRequestError,
    map_socket_error,
)
from .entities.device_twin import DeviceTwin, DeviceTwinPatch

logger = logging.getLogger("bedger.edge.client")


class UnixSocketHTTPConnection(HTTPConnection):
    """HTTPConnection subclass that communicates via UNIX domain sockets."""

    def __init__(self, unix_socket_path: str):
        super().__init__("localhost")  # dummy host
        self.unix_socket_path = unix_socket_path

    def connect(self):
        """Override to connect to a UNIX socket instead of TCP."""
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.unix_socket_path)
        except Exception as e:
            raise map_socket_error(e, self.unix_socket_path)


class Client:
    """
    Bedger Edge Client that communicates with the local agent's HTTP API
    over a UNIX socket. Matches BedgerConnection interface.
    """

    def __init__(self, config: Config = Config()):
        self._config = config
        self._connection: UnixSocketHTTPConnection | None = None

    def __enter__(self) -> Client:
        self._connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._disconnect()

    def _connect(self) -> None:
        socket_path = self._config.socket_path
        logger.info(f"Connecting to Bedger Edge API at {socket_path}")
        try:
            self._connection = UnixSocketHTTPConnection(socket_path)
        except Exception as e:
            raise ConnectionError(socket_path, e)

    def _disconnect(self) -> None:
        if self._connection:
            try:
                self._connection.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._connection = None

    def is_healthy(self) -> bool:
        """Ping the Bedger Edge API health endpoint."""
        if not self._connection:
            raise ConnectionError(self._config.socket_path)

        try:
            self._connection.request("GET", "/health")
            response = self._connection.getresponse()
            raw_data = response.read().decode("utf-8")

            if response.status != 200:
                return False

            logger.debug(f"Health response: {raw_data}")
            return True
        except Exception as e:
            return False

    def send_event(self, event_type: str, severity: entities.Severity, payload: dict[str, Any]) -> None:
        """Send a DeviceEvent to /device/events."""
        if not self._connection:
            raise ConnectionError(self._config.socket_path)

        event = DeviceEvent(event_type=event_type, severity=severity, details=payload)
        serialized = event.model_dump_json(by_alias=True).encode("utf-8")

        try:
            self._connection.request(
                "POST",
                "/device/events",
                body=serialized,
                headers={"Content-Type": "application/json"},
            )

            response = self._connection.getresponse()
            response_data = response.read().decode("utf-8")

            if response.status != 200:
                raise HTTPRequestError(response.status, response_data)

            logger.info(f"Event sent successfully: {response_data}")
        except HTTPRequestError:
            raise
        except Exception as e:
            raise SendError("Failed to send DeviceEvent", e)


class DeviceTwinClient(Client):
    """Manages device twin synchronization over the Bedger Edge API."""

    def __init__(self, config: Config = Config()) -> None:
        super().__init__(config)

    def __enter__(self) -> DeviceTwinClient:
        super().__enter__()
        self._twin = self._get_twin()
        return self

    def get_twin(self) -> DeviceTwin:
        return copy.deepcopy(self._twin)

    def _get_twin(self) -> DeviceTwin:
        """Fetch and parse the full DeviceTwin model from the Bedger Edge API."""
        if not self._connection:
            raise ConnectionError(self._config.socket_path)

        try:
            self._connection.request("GET", "/device/twin")
            response = self._connection.getresponse()
            raw_data = response.read().decode("utf-8")

            if response.status != 200:
                raise HTTPRequestError(response.status, raw_data)

            logger.debug(f"Fetched raw device twin: {raw_data}")
            twin = DeviceTwin.model_validate_json(raw_data)
            logger.info("✅ DeviceTwin loaded for device")
            return twin

        except HTTPRequestError:
            raise
        except Exception as e:
            raise SendError("Failed to get device twin", e)

    def patch(self, device_twin: DeviceTwin) -> DeviceTwin:
        if not self._connection:
            raise ConnectionError(self._config.socket_path)

        try:
            current_reported = self._twin.properties_reported.model_dump(by_alias=True)
            new_reported = device_twin.properties_reported.model_dump(by_alias=True)

            patch_ops = jsonpatch.make_patch(current_reported, new_reported)

            if not patch_ops:
                logger.info("No changes detected in reported properties; skipping patch.")
                return device_twin

            twin_patch = DeviceTwinPatch(
                patch=patch_ops,
                from_version=self._twin.version,
                to_version=self._twin.version + 1,
            )

            print(patch_ops)

            payload = json.dumps(twin_patch.model_dump(by_alias=True), ensure_ascii=False).encode("utf-8")

            self._connection.request(
                "PATCH",
                "/device/twin/reported",
                body=payload,
                headers={"Content-Type": "application/json"},
            )

            response = self._connection.getresponse()
            raw_data = response.read().decode("utf-8")

            if response.status != 200:
                raise HTTPRequestError(response.status, raw_data)

            twin = DeviceTwin.model_validate_json(raw_data)
            self._last_twin = twin
            return twin

        except HTTPRequestError:
            raise
        except Exception as e:
            raise SendError("Failed to patch reported properties", e)
