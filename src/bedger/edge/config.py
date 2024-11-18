from dataclasses import dataclass


@dataclass
class Config:
    socket_path: str = "/tmp/bedger.sock"

    max_payload_size: int = 1024 * 1024  # 1 MB
