from typing import List, Optional

from pydantic import BaseModel


class FilterParams(BaseModel):
    """
    Generic parameters for filtering queries.
    """

    search: Optional[str] = None
    data_uses: Optional[List[str]] = None
    data_categories: Optional[List[str]] = None
    data_subjects: Optional[List[str]] = None
