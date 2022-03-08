# type: ignore

"""
Contains all of the SqlAlchemy models for the Fides resources.
"""

from typing import Dict

from sqlalchemy import (
    ARRAY,
    JSON,
    Column,
    Integer,
    String,
    Text,
    type_coerce,
    TypeDecorator,
    cast,
)
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime

from fidesctl.core.config import FidesctlConfig, get_config

CONFIG: FidesctlConfig = get_config()


class SqlModelBase:
    """
    This is the base class used to describe columns that every object should have.
    """

    id = Column(Integer, primary_key=True, index=True, unique=True, autoincrement=True)


class FidesBase(SqlModelBase):
    """
    The base SQL model for all top-level Fides Resources.
    """

    fides_key = Column(String, primary_key=True, index=True, unique=True)
    organization_fides_key = Column(Text)
    name = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


SqlAlchemyBase = declarative_base(cls=SqlModelBase)


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


# Privacy Types
class DataCategory(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the DataCategory resource.
    """

    __tablename__ = "data_categories"

    parent_key = Column(Text)


class DataQualifier(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the DataQualifier resource.
    """

    __tablename__ = "data_qualifiers"

    parent_key = Column(Text)


class DataSubject(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the DataSubject resource.
    """

    __tablename__ = "data_subjects"


class DataUse(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the DataUse resource.
    """

    __tablename__ = "data_uses"

    parent_key = Column(Text)
    legal_basis = Column(Text)
    recipients = Column(ARRAY(String))


# Dataset
class Dataset(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the Dataset resource.
    """

    __tablename__ = "datasets"

    meta = Column(JSON)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(String)
    collections = Column(JSON)
    joint_controller = Column(PGEncryptedString, nullable=True)
    retention = Column(String)
    third_country_transfers = Column(ARRAY(String))


# Evaluation
class Evaluation(SqlAlchemyBase):
    """
    The SQL model for the Evaluation resource.
    """

    __tablename__ = "evaluations"

    fides_key = Column(String, primary_key=True, index=True, unique=True)
    status = Column(String)
    violations = Column(JSON)
    message = Column(String)


# Organization
class Organization(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the Organization resource.
    """

    # It inherits this from FidesModel but Organization's don't have this field
    __tablename__ = "organizations"

    organization_parent_key = Column(String, nullable=True)
    controller = Column(PGEncryptedString, nullable=True)
    data_protection_officer = Column(PGEncryptedString, nullable=True)
    fidesctl_meta = Column(JSON)
    representative = Column(PGEncryptedString, nullable=True)
    security_policy = Column(String, nullable=True)


# Policy
class Policy(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the Policy resource.
    """

    __tablename__ = "policies"

    rules = Column(JSON)


# Registry
class Registry(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the Registry resource.
    """

    __tablename__ = "registries"


# System
class System(SqlAlchemyBase, FidesBase):
    """
    The SQL model for the system resource.
    """

    __tablename__ = "systems"

    registry_id = Column(String)
    meta = Column(JSON)
    fidesctl_meta = Column(JSON)
    system_type = Column(String)
    system_dependencies = Column(ARRAY(String))
    joint_controller = Column(PGEncryptedString, nullable=True)
    # department: Column(String, nullable=True)
    third_country_transfers = Column(ARRAY(String))
    privacy_declarations = Column(JSON)
    administrating_department = Column(String)


sql_model_map: Dict = {
    "data_category": DataCategory,
    "data_qualifier": DataQualifier,
    "data_subject": DataSubject,
    "data_use": DataUse,
    "dataset": Dataset,
    "organization": Organization,
    "policy": Policy,
    "registry": Registry,
    "system": System,
    "evaluation": Evaluation,
}
