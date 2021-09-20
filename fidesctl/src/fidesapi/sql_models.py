from typing import Dict

from sqlalchemy import Column, Integer, Text, String, ARRAY, ForeignKey, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import sqlalchemy.ext.declarative


class SqlModelBase:
    id = Column(Integer, primary_key=True, index=True)


class FidesBase(SqlModelBase):
    """The base SQL model for all Fides Resources."""

    fides_key = Column(postgresql.VARCHAR(200), primary_key=True, index=True)
    organization_fides_key = Column(Text)
    name = Column(Text)
    description = Column(Text)


SqlAlchemyBase = sqlalchemy.ext.declarative.declarative_base()


class DataCategory(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_category"
    parent_key = Column(Text)


class DataQualifier(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_qualifier"


class DataSubject(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_subject"


class DataUse(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_use"
    parent_key = Column(Text)


# Dataset
class Dataset(FidesBase, SqlAlchemyBase):
    __tablename__ = "dataset"
    meta = Column(JSON)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(ARRAY(String))
    location = Column(String)
    dataset_type = Column(String)
    fields = relationship("DatasetField")


class DatasetField(SqlAlchemyBase, SqlModelBase):
    __tablename__ = "dataset_field"
    parent_id = Column(Integer, ForeignKey("dataset.id"))
    name = Column(String)
    description = Column(String)
    path = Column(String)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(ARRAY(String))


# Evaluation
class Evaluation(SqlAlchemyBase, SqlModelBase):
    __tablename__ = "evaluation"
    status = Column(String)
    details = Column(ARRAY(String))
    message = Column(String)


# Organization
class Organization(SqlAlchemyBase, FidesBase):
    # It inherits this from FidesModel but Organization's don't have this field
    __tablename__ = "organization"
    organiztion_parent_key = Column(String, nullable=True)


# Policy
class Policy(SqlAlchemyBase, FidesBase):
    __tablename__ = "policy"
    rules = relationship("PolicyRule")


class PolicyRule(FidesBase, SqlAlchemyBase):
    __tablename__ = "policy_rule"
    parent_id = Column(Integer, ForeignKey("policy.id"))
    data_categories = relationship("PrivacyRule", back_populates="policy_rule")
    data_uses = relationship("PrivacyRule", back_populates="policy_rule")
    data_subjects = relationship("PrivacyRule", back_populates="policy_rule")
    data_qualifier = Column(String)
    action = Column(String)


class PrivacyRule(SqlAlchemyBase, SqlModelBase):
    __tablename__ = "privacy_rule"
    parent_id = Column(Integer, ForeignKey("policy_rule.id"))
    inclusion = Column(String)
    values = Column(ARRAY(String))


# Registry
class Registry(FidesBase, SqlAlchemyBase):
    __tablename__ = "registry"


# System
class System(FidesBase, SqlAlchemyBase):
    __tablename__ = "system"
    registry_id = Column(String)
    meta = Column(JSON)
    system_type = Column(String)
    system_dependencies = Column(ARRAY(String))
    privacy_declarations = relationship("PrivacyDeclaration")


class PrivacyDeclaration(SqlAlchemyBase, SqlModelBase):
    __tablename__ = "privacy_declaration"
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
    "organization": Organization,
    "policy": Policy,
    "registry": Registry,
    "system": System,
}
