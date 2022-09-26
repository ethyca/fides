# pylint: disable=E1101
from enum import Enum as EnumType
from typing import Any, Dict, List, Optional, Tuple, Union

from fideslang import DEFAULT_TAXONOMY
from fideslang.models import DataCategory as FideslangDataCategory
from fideslib.db.base_class import Base, FidesBase
from fideslib.models.client import ClientDetail
from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session, backref, declared_attr, relationship  # type: ignore
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fidesops.ops import common_exceptions
from fidesops.ops.common_exceptions import WebhookOrderException
from fidesops.ops.core.config import config
from fidesops.ops.db.base_class import JSONTypeOverride
from fidesops.ops.models.connectionconfig import ConnectionConfig
from fidesops.ops.models.storage import StorageConfig
from fidesops.ops.schemas.shared_schemas import FidesOpsKey
from fidesops.ops.util.data_category import _validate_data_category


class CurrentStep(EnumType):
    pre_webhooks = "pre_webhooks"
    access = "access"
    erasure = "erasure"
    erasure_email_post_send = "erasure_email_post_send"
    post_webhooks = "post_webhooks"


class ActionType(str, EnumType):
    """The purpose of a particular privacy request"""

    access = "access"
    consent = "consent"
    erasure = "erasure"
    update = "update"


class DrpAction(EnumType):
    """
    Enum to hold valid DRP actions. For more details, see:
    https://github.com/consumer-reports-digital-lab/data-rights-protocol#301-supported-rights-actions
    """

    access = "access"
    deletion = "deletion"
    # below are not supported
    sale_opt_out = "sale:opt_out"
    sale_opt_in = "sale:opt_in"
    access_categories = "access:categories"
    access_specific = "access:specific"


def _validate_drp_action(drp_action: Optional[str]) -> None:
    """Check that DRP action is supported"""
    if not drp_action:
        return
    if drp_action in [
        DrpAction.sale_opt_in.value,
        DrpAction.sale_opt_out.value,
        DrpAction.access_categories.value,
        DrpAction.access_specific.value,
    ]:
        raise common_exceptions.DrpActionValidationError(
            f"{drp_action} action is not supported at this time."
        )


def _validate_rule(
    action_type: Optional[str],
    storage_destination_id: Optional[str],
    masking_strategy: Optional[Dict[str, Union[str, Dict[str, str]]]],
) -> None:
    """Check that the rule's action_type and storage_destination are valid."""
    if not action_type:
        raise common_exceptions.RuleValidationError("action_type is required.")
    if action_type == ActionType.erasure.value:
        if storage_destination_id is not None:
            raise common_exceptions.RuleValidationError(
                "Erasure Rules cannot have storage destinations."
            )
        if masking_strategy is None:
            raise common_exceptions.RuleValidationError(
                "Erasure Rules must have masking strategies."
            )
    if action_type == ActionType.access.value:
        if storage_destination_id is None:
            raise common_exceptions.RuleValidationError(
                "Access Rules must have a storage destination."
            )
    if action_type in [ActionType.consent.value, ActionType.update.value]:
        raise common_exceptions.RuleValidationError(
            f"{action_type} Rules are not supported at this time."
        )


class Policy(Base):
    """A set of constraints to apply to a privacy request"""

    name = Column(String, unique=True, nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    drp_action = Column(EnumColumn(DrpAction), index=True, unique=True, nullable=True)
    execution_timeframe = Column(Integer, nullable=True)
    client_id = Column(
        String,
        ForeignKey(ClientDetail.id_field_path),
        nullable=False,
    )
    client = relationship(
        ClientDetail,
        backref="policies",
    )  # Which client created the Policy

    @classmethod
    def create_or_update(cls, db: Session, *, data: Dict[str, Any]) -> FidesBase:
        """Overrides base create or update to add custom error for drp action already exists"""
        db_obj = cls.get_by_key_or_id(db=db, data=data)
        if hasattr(cls, "drp_action"):
            data["drp_action"] = data.get("drp_action", None)
            _validate_drp_action(data["drp_action"])
        if db_obj:
            db_obj.update(db=db, data=data)
        else:
            db_obj = cls.create(db=db, data=data)
        return db_obj

    def delete(self, db: Session) -> Optional[FidesBase]:
        """Cascade delete all rules on deletion of a Policy."""
        _ = [rule.delete(db=db) for rule in self.rules]
        return super().delete(db=db)

    def get_erasure_target_categories(self) -> List[str]:
        """Returns all data categories that are the target of erasure rules."""
        erasure_categories = []
        for rule in self.rules:
            if rule.action_type == ActionType.erasure:
                erasure_categories.extend(rule.get_target_data_categories())

        return erasure_categories

    def get_rules_for_action(self, action_type: ActionType) -> List["Rule"]:
        """Returns all Rules related to this Policy filtered by `action_type`."""
        return [rule for rule in self.rules if rule.action_type == action_type]


def _get_ref_from_taxonomy(fides_key: FidesOpsKey) -> FideslangDataCategory:
    """Returns the DataCategory model from the DEFAULT_TAXONOMY corresponding to fides_key."""
    for item in DEFAULT_TAXONOMY.data_category:
        if item.fides_key == fides_key:
            return item

    raise common_exceptions.DataCategoryNotSupported(
        f"The data category {fides_key} has no Fideslang reference."
    )


def _is_ancestor_of_contained_categories(
    fides_key: FidesOpsKey,
    data_categories: List[str],
) -> Tuple[bool, Optional[str]]:
    """
    Returns True if `fides_key` is an ancestor of any item in `data_categories`.
    Warning that this algorithm is recursive, is susceptible to infinite loops and
    other misconfigurations in the underlying DEFAULT_TAXONOMY imported from fideslang.

    TODO: Should we memoize this function?
    """
    ref = _get_ref_from_taxonomy(fides_key=fides_key)
    if ref.parent_key:
        if ref.parent_key in data_categories:
            return True, ref.parent_key

        return _is_ancestor_of_contained_categories(
            fides_key=ref.parent_key,
            data_categories=data_categories,
        )

    return False, None


def _validate_rule_target_collection(target_categories: List[str]) -> None:
    """
    Validates that no erasure rules within the Policy have conflicting data category targets:
        - We cannot mask the same data categories multiple times
        - We cannot perform separate masking upon a data category's sub-categories
    """

    for cat in target_categories:
        # Here we check that `cat` is not an ancestor of any other category within `target_categories`
        is_ancestor, ancestor_fides_key = _is_ancestor_of_contained_categories(
            fides_key=cat,  # type: ignore
            data_categories=target_categories,
        )
        if is_ancestor:
            raise common_exceptions.PolicyValidationError(
                f"Policy rules are invalid, action conflict in erasure rules detected for categories {cat} and {ancestor_fides_key}"
            )


class Rule(Base):
    """
    The constraints to apply to data that matches the RuleTargets of Privacy Requests:
        - How to action the privacy request
        - Where to upload any retrieved data
    """

    name = Column(String, unique=True, nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    policy_id = Column(
        String,
        ForeignKey(Policy.id_field_path),
        nullable=False,
    )
    policy = relationship(
        Policy,
        backref="rules",
    )
    action_type = Column(
        EnumColumn(ActionType),
        nullable=False,
    )
    masking_strategy = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                config.security.app_encryption_key,
                AesGcmEngine,
                "pkcs5",
            )
        ),
        nullable=True,
    )  # Type bytea in the db
    storage_destination_id = Column(
        String,
        ForeignKey(StorageConfig.id_field_path),
        nullable=True,
    )
    storage_destination = relationship(
        StorageConfig,
        backref="rules",
    )
    client_id = Column(
        String,
        ForeignKey(ClientDetail.id_field_path),
        nullable=True,
    )
    client = relationship(
        ClientDetail,
        backref="rules",
    )  # Which client created the Rule

    def save(self, db: Session) -> FidesBase:
        """Validate this object's data before deferring to the superclass on save"""
        _validate_rule(
            action_type=self.action_type,
            storage_destination_id=self.storage_destination_id,
            masking_strategy=self.masking_strategy,
        )
        return super().save(db=db)

    @classmethod
    def create(cls, db: Session, *, data: Dict[str, Any]) -> FidesBase:
        """Validate this object's data before deferring to the superclass on update"""
        _validate_rule(
            action_type=data.get("action_type"),
            storage_destination_id=data.get("storage_destination_id"),
            masking_strategy=data.get("masking_strategy"),
        )
        return super().create(db=db, data=data)

    def delete(self, db: Session) -> Optional[FidesBase]:
        """Cascade delete all targets on deletion of a Rule."""
        _ = [target.delete(db=db) for target in self.targets]
        return super().delete(db=db)

    def get_target_data_categories(self) -> List[str]:
        """
        Returns a list of DataCategory enum values representing the targets
        that this Rule is configured to apply to.
        """
        return [target.data_category for target in self.targets]

    @classmethod
    def create_or_update(cls, db: Session, *, data: Dict[str, Any]) -> FidesBase:
        """
        An override of `FidesBase.create_or_update` that handles the specific edge case where
        a `Rule` getting updated may be having its `policy_id` changed, potentially causing
        `Rule`s to unexpectedly bounce between `Policy`ies.
        """
        db_obj = None
        if data.get("id") is not None:
            # If `id` has been included in `data`, preference that
            db_obj = cls.get(db=db, object_id=data["id"])
            identifier = data.get("id")
        elif data.get("key") is not None:
            # Otherwise, try with `key`
            db_obj = cls.get_by(db=db, field="key", value=data["key"])
            identifier = data.get("key")

        if db_obj:
            if db_obj.policy_id != data["policy_id"]:
                raise common_exceptions.RuleValidationError(
                    f"Rule with identifier {identifier} belongs to another policy."
                )
            db_obj.update(db=db, data=data)
        else:
            db_obj = cls.create(db=db, data=data)

        return db_obj


def _validate_rule_target_name(name: str) -> None:
    """Raises an error if `name` is None"""
    if not name:
        raise common_exceptions.RuleTargetValidationError(
            "A `name` field must be supplied."
        )


class RuleTarget(Base):
    """Which data categories to apply the referenced Rule to"""

    name = Column(String, unique=True, nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    data_category = Column(
        String,
        nullable=False,
    )
    rule_id = Column(
        String,
        ForeignKey(Rule.id_field_path),
        nullable=False,
    )
    rule = relationship(
        Rule,
        backref="targets",
    )
    client_id = Column(
        String,
        ForeignKey(ClientDetail.id_field_path),
        nullable=True,
    )
    client = relationship(
        ClientDetail,
        backref="rule_targets",
    )  # Which client created this RuleTarget

    __table_args__ = (
        # NB. __table_args__ requires a Tuple
        UniqueConstraint("rule_id", "data_category", name="_rule_id_data_category_uc"),
    )

    @classmethod
    def create_or_update(cls, db: Session, *, data: Dict[str, Any]) -> FidesBase:
        """
        An override of `FidesBase.create_or_update` that handles the specific edge case where
        a `RuleTarget` getting updated may be having its `rule_id` changed, potentially causing
        `RuleTarget`s to unexpectedly bounce between `Rule`s.
        """
        db_obj = None
        if data.get("id") is not None:
            # If `id` has been included in `data`, preference that
            db_obj = cls.get(db=db, object_id=data["id"])
            identifier = data.get("id")
        elif data.get("key") is not None:
            # Otherwise, try with `key`
            db_obj = cls.get_by(db=db, field="key", value=data["key"])
            identifier = data.get("key")

        if db_obj:
            if db_obj.rule_id != data["rule_id"]:
                raise common_exceptions.RuleTargetValidationError(
                    f"RuleTarget with identifier {identifier} belongs to another rule."
                )
            db_obj.update(db=db, data=data)
        else:
            db_obj = cls.create(db=db, data=data)

        return db_obj

    @classmethod
    def create(cls, db: Session, *, data: Dict[str, Any]) -> FidesBase:
        """Validate data_category on object creation."""
        data_category = data.get("data_category")
        if not data_category:
            raise common_exceptions.RuleTargetValidationError(
                "A data_category must be supplied."
            )
        rule_id = data.get("rule_id")
        if not rule_id:
            raise common_exceptions.RuleTargetValidationError(
                "A rule_id must be supplied."
            )

        default_name = f"{rule_id}-{data_category}"
        if data.get("name") is None:
            data["name"] = default_name

        _validate_data_category(data_category=data_category)

        # This database query is necessary since we need to access all Rules and their Targets
        # associated with any given Policy, not just those in the local scope of this object.
        rule = Rule.get(db=db, object_id=rule_id)
        if not rule:
            raise common_exceptions.RuleTargetValidationError(
                f"Rule with ID {rule_id} does not exist."
            )

        if rule.action_type.value == ActionType.erasure.value:
            # If we're adding a data category to an erasure rule, we need to validate that there
            # are no conflicting actions in the erasure rules.
            erasure_categories = [data_category]
            policy = rule.policy
            if policy:
                erasure_categories.extend(rule.policy.get_erasure_target_categories())

            _validate_rule_target_collection(erasure_categories)

        return super().create(db=db, data=data)

    def save(self, db: Session) -> FidesBase:
        """Validate data_category on object save."""
        _validate_data_category(data_category=self.data_category)
        _validate_rule_target_name(name=self.name)
        return super().save(db=db)

    def update(self, db: Session, *, data: Dict[str, Any]) -> FidesBase:
        """Validate data_category on object update."""
        updated_data_category = data.get("data_category")
        if data.get("name") is None:
            # Don't pass explcit `None` through for `name` because the field
            # is non-nullable
            del data["name"]

        if (
            updated_data_category is not None
            and updated_data_category != self.data_category
        ):
            _validate_data_category(data_category=updated_data_category)
        return super().update(db=db, data=data)


class WebhookDirection(EnumType):
    """The webhook direction"""

    one_way = "one_way"  # No response expected
    two_way = "two_way"  # Response expected


class WebhookBase:
    """Mixin class to contain common fields between PolicyPreWebhooks and PolicyPostWebhooks"""

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()  # type: ignore

    name = Column(String, unique=True, nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)

    @declared_attr
    def policy_id(cls: "WebhookBase") -> Column:
        """Policy id defined as declared_attr because this is needed for FK's on mixins"""
        return Column(
            String,
            ForeignKey(Policy.id_field_path),
            nullable=False,
        )

    @declared_attr
    def connection_config_id(cls: "WebhookBase") -> Column:
        """Connection config id defined as declared_attr because this is needed for FK's on mixins"""
        return Column(
            String, ForeignKey(ConnectionConfig.id_field_path), nullable=False
        )

    direction = Column(
        EnumColumn(WebhookDirection),
        nullable=False,
    )
    order = Column(Integer, nullable=False)

    def reorder_related_webhooks(self, db: Session, new_index: int) -> None:
        """Updates the order of the current webhook, and order of related webhooks where applicable.

        For example, if you had five Pre-Execution webhooks on a Policy and you updated the order of the
        fifth webhook to be the second webhook, the second, third, fourth, and fifth Pre-Execution
        Webhooks on that Policy would likewise have their order updated.
        """

        cls = self.__class__
        webhooks = getattr(self.policy, f"{cls.prefix}_execution_webhooks").order_by(  # type: ignore
            cls.order
        )  # pylint: disable=W0143

        if new_index > webhooks.count() - 1 or new_index < 0:
            raise WebhookOrderException(
                f"Cannot set order to {new_index}: there are only {webhooks.count()} {cls.__name__}(s) defined on this Policy."
            )
        webhook_order = [webhook.key for webhook in webhooks]
        webhook_order.insert(new_index, webhook_order.pop(self.order))

        for webhook in webhooks:
            webhook.update(db=db, data={"order": webhook_order.index(webhook.key)})
        db.commit()


class PolicyPreWebhook(WebhookBase, Base):
    """The configuration to describe webhooks that run before Privacy Requests are executed for a given Policy"""

    prefix = "pre"  # For logging purposes

    connection_config = relationship(
        ConnectionConfig,
        backref="policy_pre_execution_webhooks",
    )

    policy = relationship(
        "Policy", backref=backref("pre_execution_webhooks", lazy="dynamic")
    )

    @classmethod
    def persist_obj(
        cls, db: Session, resource: "PolicyPreWebhook"
    ) -> "PolicyPreWebhook":
        """Override to have PolicyPreWebhooks not be committed to the database automatically."""
        db.add(resource)
        return resource


class PolicyPostWebhook(WebhookBase, Base):
    """The configuration to describe webhooks that run after Privacy Requests are executed for a given Policy"""

    prefix = "post"  # For logging purposes

    connection_config = relationship(
        ConnectionConfig,
        backref="policy_post_execution_webhooks",
    )

    policy = relationship(
        "Policy", backref=backref("post_execution_webhooks", lazy="dynamic")
    )

    @classmethod
    def persist_obj(
        cls, db: Session, resource: "PolicyPostWebhook"
    ) -> "PolicyPostWebhook":
        """Override to have PolicyPostWebhooks not be committed to the database automatically."""
        db.add(resource)
        return resource


WebhookTypes = Union[PolicyPreWebhook, PolicyPostWebhook]
