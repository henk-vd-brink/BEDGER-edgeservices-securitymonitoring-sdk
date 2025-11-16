from __future__ import annotations
import socket


class BedgerError(Exception):
    """Base class for all Bedger-related exceptions."""

    pass


# --- Configuration and Initialization ---


class ConfigurationError(BedgerError):
    """Raised when configuration values are missing, invalid, or inconsistent."""

    def __init__(self, message: str, path: str | None = None):
        self.path = path
        super().__init__(f"{message}{f' (path: {path})' if path else ''}")


class EnvironmentError(BedgerError):
    """Raised when the environment or system setup prevents operation (permissions, missing dirs, etc.)."""

    pass


# --- Networking / Socket Communication ---


class ConnectionError(BedgerError):
    """Raised when connection to a UNIX or network socket fails."""

    def __init__(self, socket_path: str, original_error: Exception | None = None):
        self.socket_path = socket_path
        self.original_error = original_error
        super().__init__(f"Failed to connect to socket at {socket_path}: {original_error}")


class SendError(BedgerError):
    """Raised when sending data to Bedger Edge fails."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(f"{message}{f' ({original_error})' if original_error else ''}")


class ReceiveError(BedgerError):
    """Raised when receiving acknowledgment or response fails."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(f"{message}{f' ({original_error})' if original_error else ''}")


# --- HTTP API Errors ---


class HTTPRequestError(BedgerError):
    """Raised for failed HTTP requests to the local Bedger Edge API."""

    def __init__(self, status_code: int, response: str):
        self.status_code = status_code
        self.response = response
        super().__init__(f"Bedger API returned HTTP {status_code}: {response}")


class JSONSerializationError(BedgerError):
    """Raised when JSON encoding or decoding fails."""

    pass


# --- Certificates / Security ---


class CaCertificateError(BedgerError):
    """Raised when fetching or validating a CA certificate fails."""

    pass


class AuthenticationError(BedgerError):
    """Raised when authentication or provisioning fails."""

    pass


# --- Device Twin / State Sync ---


class DeviceTwinError(BedgerError):
    """Raised when device twin synchronization or persistence fails."""

    pass


class DeviceEventError(BedgerError):
    """Raised when processing or storing device events fails."""

    pass


# --- Utilities ---


def map_socket_error(err: Exception, socket_path: str) -> BedgerError:
    """Map low-level socket errors to Bedger-friendly errors."""
    if isinstance(err, FileNotFoundError):
        return ConnectionError(socket_path, original_error=err)
    elif isinstance(err, PermissionError):
        return EnvironmentError(f"Permission denied on socket {socket_path}")
    elif isinstance(err, socket.timeout):
        return ConnectionError(socket_path, original_error=err)
    else:
        return BedgerError(str(err))
