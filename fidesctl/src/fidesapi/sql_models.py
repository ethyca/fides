from typing import Dict

from sqlalchemy import Column, Integer, Text, String, ARRAY, ForeignKey, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import sqlalchemy.ext.declarative


class SqlModelBase:
    """This is the base class used to describe columns that every object should have."""

    id = Column(Integer, primary_key=True, index=True, unique=True, autoincrement=True)


class FidesBase(SqlModelBase):
    """The base SQL model for all top-level Fides Resources."""

    fides_key = Column(
        postgresql.VARCHAR(200), primary_key=True, index=True, unique=True
    )
    organization_fides_key = Column(Text)
    name = Column(Text)
    description = Column(Text)


SqlAlchemyBase = sqlalchemy.ext.declarative.declarative_base(cls=SqlModelBase)


class DataCategory(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_categories"

    fides_key = Column(postgresql.VARCHAR(200), primary_key=True, index=True)
    organization_fides_key = Column(Text)
    name = Column(Text)
    description = Column(Text)
    parent_key = Column(Text)


class DataQualifier(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_qualifiers"


class DataSubject(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_subjects"


class DataUse(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_uses"

    parent_key = Column(Text)


# Dataset
class Dataset(SqlAlchemyBase, FidesBase):
    __tablename__ = "datasets"

    meta = Column(JSON)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(ARRAY(String))
    location = Column(String)
    dataset_type = Column(String)

    fields = relationship("DatasetField")


class DatasetField(SqlAlchemyBase):
    __tablename__ = "dataset_fields"

    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    name = Column(String)
    description = Column(String)
    path = Column(String)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(ARRAY(String))


# Evaluation
class Evaluation(SqlAlchemyBase):
    __tablename__ = "evaluations"

    status = Column(String)
    details = Column(ARRAY(String))
    message = Column(String)


# Organization
class Organization(SqlAlchemyBase, FidesBase):
    # It inherits this from FidesModel but Organization's don't have this field
    __tablename__ = "organizations"

    organiztion_parent_key = Column(String, nullable=True)


# Policy
class Policy(SqlAlchemyBase, FidesBase):
    __tablename__ = "policies"

    rules = relationship("PolicyRule")


class PolicyRule(SqlAlchemyBase):
    __tablename__ = "policy_rules"

    policy_id = Column(Integer, ForeignKey("policies.id"))
    data_categories = relationship("PrivacyRule")
    data_uses = relationship("PrivacyRule")
    data_subjects = relationship("PrivacyRule")
    data_qualifier = Column(String)
    action = Column(String)


class PrivacyRule(SqlAlchemyBase):
    __tablename__ = "privacy_rules"

    policy_rule_id = Column(Integer, ForeignKey("policy_rules.id"))
    inclusion = Column(String)
    values = Column(ARRAY(String))


# Registry
class Registry(SqlAlchemyBase, FidesBase):
    __tablename__ = "registries"


# System
class System(SqlAlchemyBase, FidesBase):
    __tablename__ = "systems"

    registry_id = Column(String)
    meta = Column(JSON)
    system_type = Column(String)
    system_dependencies = Column(ARRAY(String))
    privacy_declarations = relationship("PrivacyDeclaration")


class PrivacyDeclaration(SqlAlchemyBase):
    __tablename__ = "privacy_declarations"

    system_id = Column(Integer, ForeignKey("systems.id"))
    name = Column(String)
    data_categories = Column(ARRAY(String))
    data_use = Column(String)
    data_qualifier = Column(String)
    data_subjects = Column(ARRAY(String))
    dataset_references = Column(ARRAY(String))


sql_model_map: Dict = {
    "data_category": DataCategory,
    "data_qualifier": DataQualifier,
    "data_subject": DataSubject,
    "data_use": DataUse,
    "dataset": Dataset,
    "evaluation": Evaluation,
    "organization": Organization,
    "policy": Policy,
    "registry": Registry,
    "system": System,
}
