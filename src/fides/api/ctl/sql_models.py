# type: ignore

"""
Contains all of the SqlAlchemy models for the Fides resources.
"""

from typing import Dict

from sqlalchemy import (
    ARRAY,
    BOOLEAN,
    JSON,
    Column,
    Integer,
    String,
    Text,
    TypeDecorator,
    cast,
    type_coerce,
)
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime

from fides.core.config import FidesConfig, get_config
from fides.lib.db.base import (  # type: ignore[attr-defined]
    Base,
    ClientDetail,
    FidesUser,
    FidesUserPermissions,
)
from fides.lib.db.base_class import FidesBase as FideslibBase

CONFIG: FidesConfig = get_config()


class FidesBase(FideslibBase):
    """
    The base SQL model for all top-level Fides Resources.
    """

    fides_key = Column(String, primary_key=True, index=True, unique=True)
    organization_fides_key = Column(Text)
    tags = Column(ARRAY(String))
    name = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PGEncryptedString(TypeDecorator):
    """
    This TypeDecorator handles encrypting and decrypting values at rest
    on the database that would normally be stored as json.

    The values are explicitly cast as json then text to take advantage of
    the pgcrypto extension.
    """

    impl = BYTEA
    python_type = String

    cache_ok = True

    def __init__(self):
        super().__init__()

        self.passphrase = CONFIG.user.encryption_key

    def bind_expression(self, bindparam):
        # Needs to be a string for the encryption, however it also needs to be treated as JSON first

        bindparam = type_coerce(bindparam, JSON)

        return func.pgp_sym_encrypt(cast(bindparam, Text), self.passphrase)

    def column_expression(self, column):
        return cast(func.pgp_sym_decrypt(column, self.passphrase), JSON)

    def process_bind_param(self, value, dialect):
        pass

    def process_literal_param(self, value, dialect):
        pass

    def process_result_value(self, value, dialect):
        pass


class ClassificationDetail(Base):
    """
    The SQL model for a classification instance
    """

    __tablename__ = "cls_classification_detail"
    instance_id = Column(String(255))
    status = Column(Text)
    dataset = Column(Text)
    collection = Column(Text)
    field = Column(Text)
    labels = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    # get the details from a classification json output (likely aggregate and options etc.)


class ClassificationInstance(Base):
    """
    The SQL model for a classification instance
    """

    __tablename__ = "cls_classification_instance"

    status = Column(Text)
    organization_key = Column(Text)
    dataset_key = Column(Text)
    dataset_name = Column(Text)
    target = Column(Text)
    type = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


# Privacy Types
class DataCategory(Base, FidesBase):
    """
    The SQL model for the DataCategory resource.
    """

    __tablename__ = "ctl_data_categories"

    parent_key = Column(Text)
    is_default = Column(BOOLEAN, default=False)


class DataQualifier(Base, FidesBase):
    """
    The SQL model for the DataQualifier resource.
    """

    __tablename__ = "ctl_data_qualifiers"

    parent_key = Column(Text)
    is_default = Column(BOOLEAN, default=False)


class DataSubject(Base, FidesBase):
    """
    The SQL model for the DataSubject resource.
    """

    __tablename__ = "ctl_data_subjects"
    rights = Column(JSON, nullable=True)
    automated_decisions_or_profiling = Column(BOOLEAN, nullable=True)
    is_default = Column(BOOLEAN, default=False)


class DataUse(Base, FidesBase):
    """
    The SQL model for the DataUse resource.
    """

    __tablename__ = "ctl_data_uses"

    parent_key = Column(Text)
    legal_basis = Column(Text)
    special_category = Column(Text)
    recipients = Column(ARRAY(String))
    legitimate_interest = Column(BOOLEAN, nullable=True)
    legitimate_interest_impact_assessment = Column(String, nullable=True)
    is_default = Column(BOOLEAN, default=False)


# Dataset
class Dataset(Base, FidesBase):
    """
    The SQL model for the Dataset resource.
    """

    __tablename__ = "ctl_datasets"

    meta = Column(JSON)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(String)
    collections = Column(JSON)
    fidesctl_meta = Column(JSON)
    joint_controller = Column(PGEncryptedString, nullable=True)
    retention = Column(String)
    third_country_transfers = Column(ARRAY(String))


# Evaluation
class Evaluation(Base):
    """
    The SQL model for the Evaluation resource.
    """

    __tablename__ = "ctl_evaluations"

    fides_key = Column(String, primary_key=True, index=True, unique=True)
    status = Column(String)
    violations = Column(JSON)
    message = Column(String)


# Organization
class Organization(Base, FidesBase):
    """
    The SQL model for the Organization resource.
    """

    # It inherits this from FidesModel but Organization's don't have this field
    __tablename__ = "ctl_organizations"

    organization_parent_key = Column(String, nullable=True)
    controller = Column(PGEncryptedString, nullable=True)
    data_protection_officer = Column(PGEncryptedString, nullable=True)
    fidesctl_meta = Column(JSON)
    representative = Column(PGEncryptedString, nullable=True)
    security_policy = Column(String, nullable=True)


# Policy
class PolicyCtl(Base, FidesBase):
    """
    The SQL model for the Policy resource.
    """

    __tablename__ = "ctl_policies"

    rules = Column(JSON)


# Registry
class Registry(Base, FidesBase):
    """
    The SQL model for the Registry resource.
    """

    __tablename__ = "ctl_registries"


# System
class System(Base, FidesBase):
    """
    The SQL model for the system resource.
    """

    __tablename__ = "ctl_systems"

    registry_id = Column(String)
    meta = Column(JSON)
    fidesctl_meta = Column(JSON)
    system_type = Column(String)
    data_responsibility_title = Column(String)
    system_dependencies = Column(ARRAY(String))
    joint_controller = Column(PGEncryptedString, nullable=True)
    third_country_transfers = Column(ARRAY(String))
    privacy_declarations = Column(JSON)
    administrating_department = Column(String)
    data_protection_impact_assessment = Column(JSON)
    egress = Column(JSON)
    ingress = Column(JSON)


class SystemScans(Base):
    """
    The SQL model for System Scan instances.
    """

    __tablename__ = "plus_system_scans"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    error = Column(String, nullable=True)
    is_classified = Column(BOOLEAN, default=False, nullable=False)
    result = Column(JSON, nullable=True)
    status = Column(String, nullable=False)
    system_count = Column(Integer, autoincrement=False, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


sql_model_map: Dict = {
    "client_detail": ClientDetail,
    "data_category": DataCategory,
    "data_qualifier": DataQualifier,
    "data_subject": DataSubject,
    "data_use": DataUse,
    "dataset": Dataset,
    "fides_user": FidesUser,
    "fides_user_permissions": FidesUserPermissions,
    "organization": Organization,
    "policy": PolicyCtl,
    "registry": Registry,
    "system": System,
    "evaluation": Evaluation,
}

models_with_default_field = [
    sql_model
    for _, sql_model in sql_model_map.items()
    if hasattr(sql_model, "is_default")
]
