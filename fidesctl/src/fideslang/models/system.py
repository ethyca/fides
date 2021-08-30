from typing import Dict, List, Optional

from pydantic import BaseModel, validator

from fideslang.models.validation import sort_list_objects, no_self_reference
from fideslang.models.fides_model import FidesModel, FidesKey


class PrivacyDeclaration(BaseModel):
    name: str
    dataCategories: List[FidesKey]
    dataUse: FidesKey
    dataQualifier: FidesKey
    dataSubjects: List[FidesKey]
    datasetReferences: Optional[List[str]]


class System(FidesModel):
    registryId: Optional[int]
    metadata: Optional[Dict[str, str]]
    systemType: str
    privacyDeclarations: List[PrivacyDeclaration]
    systemDependencies: Optional[List[FidesKey]]

    _sort_privacy_declarations = validator("privacyDeclarations", allow_reuse=True)(
        sort_list_objects
    )

    _no_self_reference = validator(
        "systemDependencies", allow_reuse=True, each_item=True
    )(no_self_reference)
