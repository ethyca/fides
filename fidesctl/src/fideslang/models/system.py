from typing import Dict, List, Optional

from pydantic import BaseModel

from fideslang.models.fides_model import FidesModel


class PrivacyDeclaration(BaseModel):
    name: str
    dataCategories: List[str]
    dataUse: str
    dataQualifier: str
    dataSubjects: List[str]
    datasetReferences: Optional[List[str]]


class System(FidesModel):
    registryId: Optional[int]
    metadata: Optional[Dict[str, str]]
    systemType: str
    privacyDeclarations: List[PrivacyDeclaration]
    systemDependencies: Optional[List[str]]
