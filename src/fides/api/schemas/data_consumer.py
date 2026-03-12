from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from fides.api.schemas.data_purpose import DataPurposeResponse


class DataConsumerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    external_id: Optional[str] = None
    egress: Optional[Dict] = None
    ingress: Optional[Dict] = None
    data_shared_with_third_parties: bool = False
    third_parties: Optional[str] = None
    shared_categories: List[str] = Field(default_factory=list)
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None
    tags: List[str] = Field(default_factory=list)


class DataConsumerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    egress: Optional[Dict] = None
    ingress: Optional[Dict] = None
    data_shared_with_third_parties: Optional[bool] = None
    third_parties: Optional[str] = None
    shared_categories: Optional[List[str]] = None
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None
    tags: Optional[List[str]] = None


class DataConsumerPurposeAssignment(BaseModel):
    purpose_fides_keys: List[str]


class DataConsumerResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    type: str
    external_id: Optional[str] = None
    purposes: List[DataPurposeResponse] = Field(default_factory=list)
    system_fides_key: Optional[str] = None
    vendor_id: Optional[str] = None
    egress: Optional[Dict] = None
    ingress: Optional[Dict] = None
    data_shared_with_third_parties: Optional[bool] = None
    third_parties: Optional[str] = None
    shared_categories: Optional[List[str]] = None
    tags: List[str] = Field(default_factory=list)
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
