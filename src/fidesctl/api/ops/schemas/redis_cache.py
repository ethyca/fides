from typing import Optional

from fidesops.ops.schemas.base_class import BaseSchema
from pydantic import Extra


class PrivacyRequestIdentity(BaseSchema):
    """Some PII grouping pertaining to a human"""

    phone_number: Optional[str] = None
    email: Optional[str] = None

    class Config:
        """Only allow phone_number and email to be supplied"""

        extra = Extra.forbid
