from pydantic import BaseModel


class DeviceTag(BaseModel):
    name: str
    value: str
