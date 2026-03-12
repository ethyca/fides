from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DataProducerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    external_id: Optional[str] = None
    monitor_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None


class DataProducerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    monitor_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None


class DataProducerMemberAssignment(BaseModel):
    user_ids: List[str]


class DataProducerResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    external_id: Optional[str] = None
    monitor_id: Optional[str] = None
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[Dict] = None
    member_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
