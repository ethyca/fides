from typing import Dict, List, Optional

from pydantic import BaseModel

from fidesctl.lang.models.fides_model import FidesModel


class PrivacyDeclaration(BaseModel):
    name: str
    dataCategories: List[str]
    dataUse: str
    dataQualifier: str
    dataSubjects: List[str]
    datasetReferences: Optional[List[str]]


class System(FidesModel):
    id: Optional[int]
    organizationId: int
    registryId: Optional[int]
    metadata: Optional[Dict[str, str]]
    systemType: str
    name: str
    description: str
    privacyDeclarations: Optional[List[PrivacyDeclaration]]
    systemDependencies: Optional[List[str]]
