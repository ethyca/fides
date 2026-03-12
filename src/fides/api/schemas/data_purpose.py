from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DataPurposeCreate(BaseModel):
    fides_key: str
    name: str
    description: Optional[str] = None
    organization_fides_key: Optional[str] = "default_organization"
    tags: Optional[List[str]] = None
    data_use: str
    data_subject: Optional[str] = None
    data_categories: List[str] = Field(default_factory=list)
    legal_basis_for_processing: Optional[str] = None
    flexible_legal_basis_for_processing: bool = True
    special_category_legal_basis: Optional[str] = None
    impact_assessment_location: Optional[str] = None
    retention_period: Optional[str] = None
    features: List[str] = Field(default_factory=list)


class DataPurposeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data_use: Optional[str] = None
    data_subject: Optional[str] = None
    data_categories: Optional[List[str]] = None
    legal_basis_for_processing: Optional[str] = None
    flexible_legal_basis_for_processing: Optional[bool] = None
    special_category_legal_basis: Optional[str] = None
    impact_assessment_location: Optional[str] = None
    retention_period: Optional[str] = None
    features: Optional[List[str]] = None


class DataPurposeResponse(BaseModel):
    id: str
    fides_key: str
    name: str
    description: Optional[str] = None
    organization_fides_key: Optional[str] = None
    tags: Optional[List[str]] = None
    data_use: str
    data_subject: Optional[str] = None
    data_categories: List[str]
    legal_basis_for_processing: Optional[str] = None
    flexible_legal_basis_for_processing: bool
    special_category_legal_basis: Optional[str] = None
    impact_assessment_location: Optional[str] = None
    retention_period: Optional[str] = None
    features: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
