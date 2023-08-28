"""Tasks that represent units of work for Privacy Requests."""
from __future__ import annotations

from enum import Enum as EnumType
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from fideslang.models import DataCategory as FideslangDataCategory
from fideslang.models import Dataset as FideslangDataset
from pydantic import BaseModel
from sqlalchemy import ARRAY, BOOLEAN, JSON, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    cast,
    type_coerce,
)
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime

from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.db.base_class import Base
from fides.api.db.base_class import FidesBase as FideslibBase
from fides.api.models.fides_user import FidesUser
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.config import CONFIG


# class Tasks(Base):
#     """
#     The SQL model for a Task.
#     """

#     __tablename__ = "tasks"
#     privacy_request_id = Column(
#         String,
#         ForeignKey(PrivacyRequest.id),
#         nullable=False,
#     )
#     status = Column(Text)
#     dataset = Column(Text)
#     collection = Column(Text)
#     field = Column(Text)
#     labels = Column(JSON)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(
#         DateTime(timezone=True),
#         server_default=func.now(),
#         onupdate=func.now(),
#     )
