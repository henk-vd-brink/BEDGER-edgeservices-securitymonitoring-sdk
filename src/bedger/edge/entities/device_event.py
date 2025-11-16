from __future__ import annotations

import json
from typing import Dict, Any, Annotated
from pydantic import BaseModel, Field, field_validator, field_serializer
from .severity import Severity


class DeviceEvent(BaseModel):
    """
    Represents a stored or transmitted device event.
    This model is compatible with the local /device/events API.
    """

    event_type: Annotated[
        str,
        Field(
            description="Event type in PascalCase format",
            pattern=r"^[A-Z][a-zA-Z0-9]*$",
        ),
    ]
    severity: Severity
    details: Annotated[
        Dict[str, Any],
        Field(description="Event-specific details, must be JSON serializable"),
    ]

    @field_validator("details")
    @classmethod
    def validate_details(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        try:
            json.dumps(value)
        except TypeError:
            raise ValueError("details must be a JSON serializable dictionary")
        return value

    @field_serializer("severity")
    def serialize_severity(self, severity: Severity) -> str:
        return severity.value
