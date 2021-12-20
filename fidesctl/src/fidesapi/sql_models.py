"""
Contains all of the SqlAlchemy models for the Fides resources.
"""

from typing import Dict

from sqlalchemy import ARRAY, JSON, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime


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
    system_type = Column(String)
    system_dependencies = Column(ARRAY(String))
    privacy_declarations = Column(JSON)


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
