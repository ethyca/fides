from typing import Dict

from sqlalchemy import Column, Integer, Text, String, ARRAY, JSON
from sqlalchemy.dialects import mysql
import sqlalchemy.ext.declarative


class FidesBase:
    """The base SQL model for all Fides Resources."""

    id = Column(Integer, primary_key=True, index=True)
    fides_key = Column(mysql.VARCHAR(200), primary_key=True, index=True)
    organization_fides_key = Column(Text)
    name = Column(Text)
    description = Column(Text)


SqlAlchemyBase = sqlalchemy.ext.declarative.declarative_base(cls=FidesBase)


class DataCategory(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_category"
    parent_key = Column(Text(length=100))


class DataQualifier(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_qualifier"


class DataSubject(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_subject"


class DataUse(SqlAlchemyBase, FidesBase):
    __tablename__ = "data_use"
    parent_key = Column(Text(length=100))


# Dataset
class DatasetField(SqlAlchemyBase):
    __tablename__ = "dataset_field"
    name = Column(String)
    description = Column(String)
    path = Column(String)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(ARRAY(String))


class Dataset(SqlAlchemyBase, FidesBase):
    __tablename__ = "dataset"
    metadata = Column(JSON)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(ARRAY(String))
    location = Column(String)
    dataset_type = Column(String)
    fields: List[DatasetField]


# Evaluation
class Evaluation(SqlAlchemyBase):
    __tablename__ = "evaluation"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String)
    details = Column(ARRAY(String))
    message = Column(String)


# Organization
class Organization(SqlAlchemyBase, FidesBase):
    # It inherits this from FidesModel but Organization's don't have this field
    __tablename__ = "organization"
    organiztion_parent_key = Column(String, nullable=True)


# Policy
class PrivacyRule(SqlAlchemyBase):
    __tablename__ = "privacy_rule"
    inclusion: InclusionEnum
    values: List[FidesKey]


class PolicyRule(FidesBase, SqlAlchemyBase):
    __tablename__ = "policy_rule"
    data_categories: PrivacyRule
    data_uses: PrivacyRule
    data_subjects: PrivacyRule
    data_qualifier: FidesKey
    action: ActionEnum


class Policy(SqlAlchemyBase, FidesBase):
    __tablename__ = "policy"
    rules: List[PolicyRule]


# Registry
class Registry(FidesBase, SqlAlchemyBase):
    __tablename__ = "registry"


# System
class PrivacyDeclaration(SqlAlchemyBase):
    __tablename__ = "privacy_declaration"
    name = Column(String)
    data_categories = Column(ARRAY(String))
    data_use = Column(String)
    data_qualifier = Column(String)
    data_subjects = Column(ARRAY(String))
    dataset_references = Column(ARRAY(String))


class System(FidesBase, SqlAlchemyBase):
    __tablename__ = "system"
    registry_id = Column(String)
    metadata = Column(JSON)
    system_type = Column(String)
    system_dependencies = Column(ARRAY(String))
    privacy_declarations: List[PrivacyDeclaration]


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
