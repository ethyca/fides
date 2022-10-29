import logging
from typing import Any, Dict, Optional, Set

from fideslib.db.base_class import Base
from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from fides.api.ops.common_exceptions import ValidationError

from fides.api.ops.schemas.shared_schemas import FidesOpsKey

logger = logging.getLogger(__name__)


class UserRegistration(Base):
    """
    Stores registration status of a particular Fides deployment.
    """

    user_email = Column(String, nullable=True)
    user_organization = Column(String, nullable=True)
    analytics_id = Column(String, unique=True, nullable=False)
    opt_in = Column(Boolean, nullable=False, default=False)
