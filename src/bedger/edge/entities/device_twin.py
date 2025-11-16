from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_serializer


class PropertyMetaData(BaseModel):
    """Metadata describing when and how a property set was last updated."""

    short_hash: Optional[str] = Field(
        None,
        alias="$short_hash",
        description="Short 8-character hash representing the content state of the property set.",
    )
    last_updated: Optional[datetime] = Field(
        None,
        alias="$last_updated",
        description="Timestamp when this property set was last updated.",
    )

    # Serialize datetimes to ISO 8601 for JSON compatibility
    @field_serializer("last_updated")
    def serialize_last_updated(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Properties(BaseModel):
    """Represents either desired or reported property groups for device modules."""

    modules: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Arbitrary key/value structure for per-module properties.",
    )
    metadata: Optional[PropertyMetaData] = Field(
        None,
        alias="$metadata",
        description="Metadata tracking changes for this property group.",
    )

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class DeviceTwin(BaseModel):
    """Data-only representation of a Device Twin document as received from the edge or cloud."""

    version: Optional[int] = Field(
        default=None,
        description="Version number of this twin document.",
    )

    properties_desired: Optional[Properties] = Field(
        None,
        alias="properties.desired",
        description="Desired properties defined by the cloud (target configuration).",
    )
    properties_reported: Optional[Properties] = Field(
        None,
        alias="properties.reported",
        description="Reported properties coming from the device (actual state).",
    )

    metadata: Optional[PropertyMetaData] = Field(
        None,
        alias="$metadata",
        description="Overall metadata for the combined twin.",
    )

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={datetime: lambda v: v.isoformat()},  # ensure datetime → ISO string
    )

    def model_dump(self, *args, **kwargs):
        """Force by_alias=True unless explicitly overridden."""
        kwargs.setdefault("by_alias", True)
        return super().model_dump(*args, **kwargs)


class DeviceTwinPatch(BaseModel):
    """Data-only representation of a Device Twin patch (incremental update)."""

    patch: List[Dict[str, Any]] = Field(
        ...,
        description="JSON Patch operations to apply to the twin (RFC 6902).",
    )
    from_version: int = Field(
        ...,
        description="Source version number before applying this patch.",
    )
    to_version: int = Field(
        ...,
        description="Target version number after applying this patch.",
    )

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )
