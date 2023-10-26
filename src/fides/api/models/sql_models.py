# type: ignore

"""
Contains all of the SqlAlchemy models for the Fides resources.
"""

from __future__ import annotations

from enum import Enum as EnumType
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from fideslang.models import DataCategory as FideslangDataCategory
from fideslang.models import Dataset as FideslangDataset
from pydantic import BaseModel
from sqlalchemy import BOOLEAN, JSON, Column
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
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, BYTEA
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime
from typing_extensions import Protocol, runtime_checkable

from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.db.base_class import Base
from fides.api.db.base_class import FidesBase as FideslibBase
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.config import get_config

CONFIG = get_config()


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


DataCategoryType = TypeVar("DataCategoryType", bound="DataCategory")


# Privacy Types
class DataCategory(Base, FidesBase):
    """
    The SQL model for the DataCategory resource.
    """

    __tablename__ = "ctl_data_categories"

    parent_key = Column(Text)
    active = Column(BOOLEAN, default=True, nullable=False)

    # Default Fields
    is_default = Column(BOOLEAN, default=False)
    version_added = Column(Text)
    version_deprecated = Column(Text)
    replaced_by = Column(Text)

    @classmethod
    def from_fideslang_obj(
        cls, data_category: FideslangDataCategory
    ) -> DataCategoryType:
        return cls(
            fides_key=data_category.fides_key,
            organization_fides_key=data_category.organization_fides_key,
            tags=data_category.tags,
            name=data_category.name,
            description=data_category.description,
            parent_key=data_category.parent_key,
            is_default=data_category.is_default,
        )


class DataQualifier(Base, FidesBase):
    """
    The SQL model for the DataQualifier resource.
    """

    __tablename__ = "ctl_data_qualifiers"

    parent_key = Column(Text)
    active = Column(BOOLEAN, default=True, nullable=False)

    # Default Fields
    is_default = Column(BOOLEAN, default=False)
    version_added = Column(Text)
    version_deprecated = Column(Text)
    replaced_by = Column(Text)


class DataSubject(Base, FidesBase):
    """
    The SQL model for the DataSubject resource.
    """

    __tablename__ = "ctl_data_subjects"
    rights = Column(JSON, nullable=True)
    automated_decisions_or_profiling = Column(BOOLEAN, nullable=True)
    active = Column(BOOLEAN, default=True, nullable=False)

    # Default Fields
    is_default = Column(BOOLEAN, default=False)
    version_added = Column(Text)
    version_deprecated = Column(Text)
    replaced_by = Column(Text)


class DataUse(Base, FidesBase):
    """
    The SQL model for the DataUse resource.
    """

    __tablename__ = "ctl_data_uses"

    parent_key = Column(Text)
    legal_basis = Column(
        Text
    )  # Deprecated in favor of PrivacyDeclaration.legal_basis_for_processing
    special_category = Column(
        Text
    )  # Deprecated in favor of PrivacyDeclaration.special_category_legal_basis
    recipients = Column(
        ARRAY(String)
    )  # Deprecated in favor of PrivacyDeclaration.third_parties
    legitimate_interest = Column(BOOLEAN, nullable=True)  # Deprecated
    legitimate_interest_impact_assessment = Column(
        String, nullable=True
    )  # Deprecated in favor of PrivacyDeclaration.legal_basis_for_processing
    active = Column(BOOLEAN, default=True, nullable=False)

    # Default Fields
    is_default = Column(BOOLEAN, default=False)
    version_added = Column(Text)
    version_deprecated = Column(Text)
    replaced_by = Column(Text)

    @staticmethod
    def get_parent_uses_from_key(data_use_key: str) -> Set[str]:
        """
        Utility method to traverse "up" the taxonomy hierarchy and unpack
        a given data use fides key into a set of fides keys that include its
        parent fides keys.

        The utility takes a fides key string input to make the method more applicable -
        since in many spots of our application we do not have a true `DataUse` instance,
        just a "soft" reference to its fides key.

        Example inputs and outputs:
            - `a.b.c` --> [`a.b.c`, `a.b`, `a`]
            - `a` --> [`a`]
        """
        parent_uses = {data_use_key}
        while data_use_key := data_use_key.rpartition(".")[0]:
            parent_uses.add(data_use_key)
        return parent_uses


# Dataset
class Dataset(Base, FidesBase):
    """
    The SQL model for the Dataset resource.
    """

    __tablename__ = "ctl_datasets"

    meta = Column(JSON)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(String)  # Deprecated
    collections = Column(JSON)
    fides_meta = Column(JSON)
    joint_controller = Column(
        PGEncryptedString, nullable=True
    )  # Deprecated in favor of Systems.joint_controller_info
    retention = Column(
        String
    )  # Deprecated in favor of PrivacyDeclaration.retention_period
    third_country_transfers = Column(
        ARRAY(String)
    )  # Deprecated in favor of Systems.does_international_transfers

    @classmethod
    def create_from_dataset_dict(cls, db: Session, dataset: dict) -> "Dataset":
        """Add a method to create directly using a synchronous session"""
        validated_dataset: FideslangDataset = FideslangDataset(**dataset)
        ctl_dataset = cls(**validated_dataset.dict())
        db.add(ctl_dataset)
        db.commit()
        db.refresh(ctl_dataset)
        return ctl_dataset


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
    joint_controller = Column(
        PGEncryptedString, nullable=True
    )  # Deprecated in favor of System.joint_controller_info
    data_responsibility_title = Column(
        String
    )  # Deprecated in favor of System.responsibility
    third_country_transfers = Column(
        ARRAY(String)
    )  # Deprecated in favor of System.does_international_transfers
    administrating_department = Column(String)
    data_protection_impact_assessment = Column(
        JSON
    )  # Deprecated in favor of System.requires_data_protection_assessments, System.dpa_location, and System.dpa_progress
    egress = Column(JSON)
    ingress = Column(JSON)

    vendor_id = Column(String)
    dataset_references = Column(ARRAY(String), server_default="{}", nullable=False)
    processes_personal_data = Column(BOOLEAN(), server_default="t", nullable=False)
    exempt_from_privacy_regulations = Column(
        BOOLEAN(), server_default="f", nullable=False
    )
    reason_for_exemption = Column(String)
    uses_profiling = Column(BOOLEAN(), server_default="f", nullable=False)
    legal_basis_for_profiling = Column(ARRAY(String), server_default="{}")
    does_international_transfers = Column(BOOLEAN(), server_default="f", nullable=False)
    legal_basis_for_transfers = Column(ARRAY(String), server_default="{}")
    requires_data_protection_assessments = Column(
        BOOLEAN(), server_default="f", nullable=False
    )
    dpa_location = Column(String)
    dpa_progress = Column(String)
    privacy_policy = Column(String)
    legal_name = Column(String)
    legal_address = Column(String)
    responsibility = Column(ARRAY(String), server_default="{}")
    dpo = Column(String)
    joint_controller_info = Column(String)
    data_security_practices = Column(String)
    cookie_max_age_seconds = Column(BIGINT)
    uses_cookies = Column(BOOLEAN(), default=False, server_default="f", nullable=False)
    cookie_refresh = Column(
        BOOLEAN(), default=False, server_default="f", nullable=False
    )
    uses_non_cookie_access = Column(
        BOOLEAN(), default=False, server_default="f", nullable=False
    )
    legitimate_interest_disclosure_url = Column(String)

    privacy_declarations = relationship(
        "PrivacyDeclaration",
        cascade="all, delete",
        back_populates="system",
        lazy="selectin",
    )

    data_stewards = relationship(
        "FidesUser",
        secondary="systemmanager",
        back_populates="systems",
        lazy="selectin",
    )

    connection_configs = relationship(
        "ConnectionConfig",
        back_populates="system",
        cascade="all, delete",
        uselist=False,
        lazy="selectin",
    )

    cookies = relationship(
        "Cookies", back_populates="system", lazy="selectin", uselist=True, viewonly=True
    )

    user_id = Column(String, nullable=True)

    @classmethod
    def get_data_uses(
        cls: Type[System], systems: List[System], include_parents: bool = True
    ) -> set[str]:
        """
        Get all data uses that are associated with the provided `systems`
        """
        data_uses = set()
        for system in systems:
            for declaration in system.privacy_declarations:
                if data_use := declaration.data_use:
                    if include_parents:
                        data_uses.update(DataUse.get_parent_uses_from_key(data_use))
                    else:
                        data_uses.add(data_use)
        return data_uses


class PrivacyDeclaration(Base):
    """
    The SQL model for a Privacy Declaration associated with a given System.
    """

    name = Column(
        String, index=True, nullable=True
    )  # labeled as Processing Activity in the UI
    ### keep egress/ingress as JSON blobs as they have always been
    egress = Column(ARRAY(String))
    ingress = Column(ARRAY(String))

    ### references to other tables, but kept as 'soft reference' strings for now
    data_use = Column(String, index=True, nullable=False)
    data_categories = Column(ARRAY(String))
    data_qualifier = Column(String)  # Deprecated
    data_subjects = Column(ARRAY(String))
    dataset_references = Column(ARRAY(String))

    features = Column(ARRAY(String), server_default="{}", nullable=False)
    legal_basis_for_processing = Column(String)
    flexible_legal_basis_for_processing = Column(BOOLEAN())
    impact_assessment_location = Column(String)
    retention_period = Column(String)
    processes_special_category_data = Column(
        BOOLEAN(), server_default="f", nullable=False
    )
    special_category_legal_basis = Column(String)
    data_shared_with_third_parties = Column(
        BOOLEAN(), server_default="f", nullable=False
    )
    third_parties = Column(String)
    shared_categories = Column(ARRAY(String), server_default="{}")

    ### proper FK references to other tables
    # System
    system_id = Column(
        String,
        ForeignKey(System.id),
        nullable=False,
        index=True,
    )
    system = relationship(System, back_populates="privacy_declarations")
    cookies = relationship(
        "Cookies", back_populates="privacy_declaration", lazy="joined", uselist=True
    )

    @classmethod
    def create(
        cls: Type[PrivacyDeclaration],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,  # this is the reason for the override
    ) -> PrivacyDeclaration:
        """Overrides base create to avoid unique check on `name` column"""
        return super().create(db=db, data=data, check_name=check_name)


class SystemModel(BaseModel):
    fides_key: str
    registry_id: str
    meta: Optional[Dict[str, Any]]
    fidesctl_meta: Optional[Dict[str, Any]]
    system_type: str
    data_responsibility_title: Optional[str]
    joint_controller: Optional[str]
    third_country_transfers: Optional[List[str]]
    privacy_declarations: Optional[Dict[str, Any]]
    administrating_department: Optional[str]
    data_protection_impact_assessment: Optional[Dict[str, Any]]
    egress: Optional[Dict[str, Any]]
    ingress: Optional[Dict[str, Any]]
    value: Optional[List[Any]]


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


@runtime_checkable
class ModelWithDefaultField(Protocol):
    is_default: bool


class AllowedTypes(str, EnumType):
    """Allowed types for custom field."""

    string = "string"
    string_list = "string[]"


class ResourceTypes(str, EnumType):
    """Resource types that can use custom fields."""

    system = "system"
    data_use = "data use"
    data_category = "data category"
    data_subject = "data subject"
    privacy_declaration = "privacy declaration"


class CustomFieldValueList(Base):
    """Allow-list definitions for custom metadata values"""

    __tablename__ = "plus_custom_field_value_list"

    name = Column(String, nullable=False)
    description = Column(String)
    allowed_values = Column(ARRAY(String))
    custom_field_definition = relationship(
        "CustomFieldDefinition",
        back_populates="allow_list",
    )

    UniqueConstraint("name")


class CustomFieldDefinition(Base):
    """Defines custom metadata for resources."""

    __tablename__ = "plus_custom_field_definition"

    name = Column(String, index=True, nullable=False)
    description = Column(String)
    field_type = Column(
        EnumColumn(AllowedTypes),
        nullable=False,
    )
    allow_list_id = Column(String, ForeignKey(CustomFieldValueList.id), nullable=True)
    resource_type = Column(EnumColumn(ResourceTypes), nullable=False)
    field_definition = Column(String)
    custom_field = relationship(
        "CustomField",
        back_populates="custom_field_definition",
        cascade="delete, delete-orphan",
    )
    allow_list = relationship(
        "CustomFieldValueList",
        back_populates="custom_field_definition",
    )
    active = Column(BOOLEAN, nullable=False, default=True)

    @classmethod
    def create(
        cls: Type[PrivacyDeclaration],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,  # this is the reason for the override
    ) -> PrivacyDeclaration:
        """
        Overrides base create to avoid unique check on `name` column
        and to cleanly handle uniqueness constraint on name/resource_type
        """
        try:
            return super().create(db=db, data=data, check_name=check_name)
        except IntegrityError as e:
            if cls.name_resource_index in str(e):
                raise KeyOrNameAlreadyExists(
                    "Custom field definitions must have unique names for a given resource type"
                )
            raise e

    def update(self, db: Session, *, data: Dict[str, Any]) -> FidesBase:
        """Overrides base update to cleanly handle uniqueness constraint on name/resource type"""
        try:
            return super().update(db=db, data=data)
        except IntegrityError as e:
            if CustomFieldDefinition.name_resource_index in str(e):
                raise KeyOrNameAlreadyExists(
                    "Custom field definitions must have unique names for a given resource type"
                )
            raise e

    # unique index on the lowername/resource type for case-insensitive name checking per resource type
    name_resource_index = (
        "ix_plus_custom_field_definition_unique_lowername_resourcetype"
    )
    __table_args__ = (
        Index(
            name_resource_index,
            resource_type,
            func.lower(name),
            unique=True,
        ),
    )


class CustomField(Base):
    """Custom metadata for resources."""

    __tablename__ = "plus_custom_field"

    resource_type = Column(EnumColumn(ResourceTypes), nullable=False)
    resource_id = Column(String, index=True, nullable=False)
    custom_field_definition_id = Column(
        String, ForeignKey(CustomFieldDefinition.id), nullable=False
    )
    value = Column(ARRAY(String))

    custom_field_definition = relationship(
        "CustomFieldDefinition",
        back_populates="custom_field",
    )

    UniqueConstraint("resource_type", "resource_id", "custom_field_definition_id")


class AuditLogResource(Base):
    """The log of user actions against fides resources."""

    __tablename__ = "audit_log_resource"

    user_id = Column(String, nullable=True, index=True)
    request_path = Column(String, nullable=True)
    request_type = Column(String, nullable=True)
    fides_keys = Column(ARRAY(String), nullable=True)
    extra_data = Column(JSON, nullable=True)


class Cookies(Base):
    """
    Stores cookies.  Cookies have a FK to system and privacy declaration. If a privacy declaration is deleted,
    the cookie can still remain linked to the system but unassociated with a data use.
    """

    name = Column(String, index=True, nullable=False)
    path = Column(String)
    domain = Column(String)

    system_id = Column(
        String, ForeignKey(System.id_field_path, ondelete="CASCADE"), index=True
    )  # If system is deleted, remove the associated cookies.

    privacy_declaration_id = Column(
        String,
        ForeignKey(PrivacyDeclaration.id_field_path, ondelete="SET NULL"),
        index=True,
    )  # If privacy declaration is deleted, just set to null and still keep this connected to the system.

    system = relationship(
        "System",
        back_populates="cookies",
        cascade="all,delete",
        uselist=False,
        lazy="selectin",
    )

    privacy_declaration = relationship(
        "PrivacyDeclaration",
        back_populates="cookies",
        uselist=False,
        lazy="joined",  # Joined is intentional, instead of selectin
    )

    __table_args__ = (
        UniqueConstraint(
            "name", "privacy_declaration_id", name="_cookie_name_privacy_declaration_uc"
        ),
    )
