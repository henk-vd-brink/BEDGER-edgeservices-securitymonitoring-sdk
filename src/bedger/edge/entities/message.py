from typing import Dict, Annotated
from pydantic import BaseModel, Field, field_validator, field_serializer
from .severity import Severity
import json


class Message(BaseModel):
    event_type: Annotated[
        str,
        Field(
            description="Event type in PascalCase format",
            pattern=r"^[A-Z][a-zA-Z0-9]*$",
        ),
    ]
    severity: Severity
    details: Annotated[Dict, Field(description="Details of the message as a JSON serializable dictionary")]

    @field_validator("details")
    @classmethod
    def validate_details(cls, value: Dict) -> Dict:
        try:
            json.dumps(value)
        except TypeError:
            raise ValueError("details must be a JSON serializable dictionary")
        return value

    @field_serializer("severity")
    def serialize_severity(self, severity: Severity) -> str:
        return severity.value
