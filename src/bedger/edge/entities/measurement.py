from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Union

from pydantic import BaseModel, Field


class DeviceMeasurement(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metric: str
    value: Union[int, float]
    unit: str

    def model_dump_json(self, **kwargs: Any) -> str:
        """
        Ensure datetime serializes to RFC3339 with Z when UTC.
        Pydantic already does ISO8601; this is just to be explicit.
        """
        return super().model_dump_json(**kwargs)