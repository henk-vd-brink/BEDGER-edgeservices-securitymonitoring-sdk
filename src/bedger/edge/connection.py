from __future__ import annotations

import json
import socket
from .config import Config
from . import entities
import logging


logger = logging.getLogger("bedger.edge.connection")


class BedgerConnection:
    def __init__(self, config: Config = Config()):
        self._config = config

        self._socket = None

    def __enter__(self) -> BedgerConnection:
        self._connect()
        return self

    def _connect(self) -> None:
        logger.info(f"Connecting to socket at {self._config.socket_path}")
        try:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(self._config.socket_path)
            logger.info("Connected to socket")
        except Exception as e:
            logger.error(f"Error connecting to socket: {e}")
            raise e

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._socket.close()

    def send_event(self, event_type, severity, payload):
        message = entities.Message(
            event_type=event_type,
            severity=severity,
            details=payload,
        )

        try:
            logger.debug("Sending message")
            self._socket.sendall(json.dumps(message).encode())

            ack = self._socket.recv(1024)
            logger.info(f"Received acknowledgment: {ack.decode()}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise e


# Example usage
if __name__ == "__main__":
    import time

    connection = BedgerConnection()

    with connection:
        for i in range(5):
            connection.send_event(
                event_type="TestEvent", severity=entities.Severity.INFO, payload={"message": f"Test message {i}"}
            )
            time.sleep(1)
