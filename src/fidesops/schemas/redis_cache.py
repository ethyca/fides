from typing import Optional

from fidesops.schemas.base_class import BaseSchema


class PrivacyRequestIdentity(BaseSchema):
    """Some PII grouping pertaining to a human"""

    phone_number: Optional[str]
    email: Optional[str]
