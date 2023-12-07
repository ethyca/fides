from typing import Dict

from fideslang.gvl.models import MappedPurpose
from pydantic import BaseModel


class PurposesResponse(BaseModel):
    purposes: Dict[str, MappedPurpose]
    special_purposes: Dict[str, MappedPurpose]
