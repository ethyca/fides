from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.privacy_request.duplicate_group import (
    DuplicateGroup,
    generate_rule_version,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.task.conditional_dependencies.sql_translator import (
    SQLConditionTranslator,
)
from fides.config.config_proxy import DuplicateDetectionSettingsProxy

ACTIONED_REQUEST_STATUSES = [
    PrivacyRequestStatus.approved,
    PrivacyRequestStatus.in_processing,
    PrivacyRequestStatus.complete,
    PrivacyRequestStatus.requires_manual_finalization,
    PrivacyRequestStatus.requires_input,
    PrivacyRequestStatus.paused,
    PrivacyRequestStatus.awaiting_email_send,
    PrivacyRequestStatus.error,
]


class DuplicateDetectionService:
    def __init__(self, db: Session):
        self.db = db

    def _create_identity_conditions(
        self, current_request: PrivacyRequest, config: DuplicateDetectionSettingsProxy
    ) -> list[Condition]:
        """Creates conditions for matching identity fields.

        For identity field matching using the EAV pattern in ProvidedIdentity, we need to match both field_name
        and hashed_value. This function creates the required nested conditions for each identity field.
        Also adds a condition for the policy_id to ensure that we are only matching requests for the same policy.
        """
        conditions: list[Condition] = []
        current_identities: dict[str, str] = {
            pi.field_name: pi.hashed_value
            for pi in current_request.provided_identities  # type: ignore [attr-defined]
            if pi.field_name in config.match_identity_fields
        }
        if len(current_identities) != len(config.match_identity_fields):
            missing_fields = [
                field
                for field in config.match_identity_fields
                if field not in current_identities.keys()
            ]
            logger.debug(
                f"Some identity fields were not found in the current request: {missing_fields}"
            )
            return []

        for field_name, hashed_value in current_identities.items():
            identity_condition = ConditionGroup(
                logical_operator=GroupOperator.and_,
                conditions=[
                    ConditionLeaf(
                        field_address="privacyrequest.provided_identities.field_name",
                        operator=Operator.eq,
                        value=field_name,
                    ),
                    ConditionLeaf(
                        field_address="privacyrequest.provided_identities.hashed_value",
                        operator=Operator.eq,
                        value=hashed_value,
                    ),
                ],
            )
            conditions.append(identity_condition)
        policy_condition = ConditionLeaf(
            field_address="privacyrequest.policy_id",
            operator=Operator.eq,
            value=current_request.policy_id,
        )
        conditions.append(policy_condition)
        return conditions

    def _create_time_window_condition(self, time_window_days: int) -> Condition:
        """Creates a condition for matching requests within a time window."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        condition = ConditionLeaf(
            field_address="privacyrequest.created_at",
            operator=Operator.gte,
            value=cutoff_date.isoformat(),
        )
        return condition

    def create_duplicate_detection_conditions(
        self,
        current_request: PrivacyRequest,
        config: DuplicateDetectionSettingsProxy,
    ) -> Optional[ConditionGroup]:
        """
        Create conditions for duplicate detection based on configuration.

        Args:
            current_request: The current privacy request to find duplicates for
            config: Duplicate detection configuration settings

        Returns:
            A ConditionGroup with AND operator, or None if no conditions can be created
        """
        if len(config.match_identity_fields) == 0:
            return None

        identity_conditions = self._create_identity_conditions(current_request, config)
        if not identity_conditions:
            return None  # Only proceed if we have identity conditions

        time_window_condition = self._create_time_window_condition(
            config.time_window_days
        )

        # Combine all conditions with AND operator
        all_conditions: list[Condition] = [*identity_conditions, time_window_condition]
        return ConditionGroup(
            logical_operator=GroupOperator.and_, conditions=all_conditions
        )

    def find_duplicate_privacy_requests(
        self,
        current_request: PrivacyRequest,
        config: DuplicateDetectionSettingsProxy,
    ) -> list[PrivacyRequest]:
        """
        Find potential duplicate privacy requests based on duplicate detection configuration.

        Uses the SQLConditionTranslator to build queries from conditions, which handles
        the ProvidedIdentity relationship using SQLAlchemy's .any() method.

        Args:
            current_request: The privacy request to check for duplicates
            config: Duplicate detection configuration settings

        Returns:
            List of PrivacyRequest objects that match the duplicate criteria,
            does not include the current request
        """
        condition = self.create_duplicate_detection_conditions(current_request, config)

        if condition is None:
            return []

        translator = SQLConditionTranslator(self.db)
        query = translator.generate_query_from_condition(condition)
        query = query.filter(PrivacyRequest.id != current_request.id)
        return query.all()

    def generate_dedup_key(
        self, request: PrivacyRequest, config: DuplicateDetectionSettingsProxy
    ) -> str:
        """
        Generate a dedup key for a request based on the duplicate detection settings.
        """
        current_identities: dict[str, str] = {
            pi.field_name: pi.hashed_value
            for pi in request.provided_identities  # type: ignore [attr-defined]
            if pi.field_name in config.match_identity_fields
        }
        if len(current_identities) != len(config.match_identity_fields):
            raise ValueError(
                "This request does not contain the required identity fields for duplicate detection."
            )
        return "|".join([f"{value}" for _, value in current_identities.items()])

    def verified_identity_cases(
        self, request: PrivacyRequest, duplicates: list[PrivacyRequest]
    ) -> bool:
        """
        Apply verified identity rules to determine if a request is a duplicate request.
        - If this request does not have a verified identity, it may be a duplicate if another request in the group is verified.
        - If this is the first request to be verified, it is not a duplicate request
        - If other requests identities were verified before this request, it is a duplicate request
        Args:
            request: The privacy request to check
            duplicates: The list of duplicate requests

        Returns:
            True if the request is a duplicate request, False otherwise
        """
        verified_in_group = [
            duplicate for duplicate in duplicates if duplicate.identity_verified_at
        ]

        # The request identity is not verified.
        if not request.identity_verified_at:
            if len(verified_in_group) > 0:
                logger.debug(
                    f"Request {request.id} is a duplicate: it is not verified and duplicating verified request(s) {verified_in_group}."
                )
                return True

            min_created_at = min(
                (d.created_at for d in duplicates if d.created_at), default=None
            ) or datetime.now(timezone.utc)
            request_created_at = (
                request.created_at
                if request.created_at is not None
                else datetime.now(timezone.utc)
            )
            if request_created_at < min_created_at:
                return False
            logger.debug(
                f"Request {request.id} is a duplicate: it is not verified and is not the first request to be created in the group."
            )
            return True

        # The request identity is verified.
        if not verified_in_group:
            return False

        # If this request is the first with a verified identity, it is not a duplicate.
        min_verified_at = min(
            (d.identity_verified_at for d in duplicates if d.identity_verified_at),
            default=None,
        ) or datetime.now(timezone.utc)
        request_verified_at = (
            request.identity_verified_at
            if request.identity_verified_at is not None
            else datetime.now(timezone.utc)
        )
        if request_verified_at < min_verified_at:
            return False
        logger.debug(
            f"Request {request.id} is a duplicate: it is verified but not the first request to be verified in the group."
        )
        return True

    # pylint: disable=too-many-return-statements
    def is_duplicate_request(
        self, request: PrivacyRequest, config: DuplicateDetectionSettingsProxy
    ) -> bool:
        """
        Determine if a request is a duplicate request and assigns a duplicate request group id.

        The hierarchy is:
        1. Actioned requests: if this request duplicates an actioned request, it is a duplicate.
        2. Verified identity requests:
          a. if this request has a verified identity:
            - If none of the duplicates have a verified identity, it is not a duplicate.
            - If duplicates have verified identities, but this request is the first with a verified identity, it is not a duplicate.
          b. if this request does not have a verified identity:
            - If no duplicates have a verified identity, and this was the first created request, it is not a duplicate.
        3. First created request: if this is the first created request in the group, it is not a duplicate.
        4. If no canonical requests are found (meaning all requests are marked as duplicates), this request is not a duplicate.
            - Could occur if configuration changes and previous requests were already marked as duplicates.

        Args:
            request: The privacy request to check
            config: Duplicate detection configuration settings
        Returns:
            True if the request is a duplicate request, False otherwise
        """
        duplicates = self.find_duplicate_privacy_requests(request, config)
        rule_version = generate_rule_version(config)
        try:
            dedup_key = self.generate_dedup_key(request, config)
        except ValueError as e:
            logger.debug(f"Request {request.id} is not a duplicate: {e}")
            return False

        _, duplicate_group = DuplicateGroup.get_or_create(
            db=self.db, data={"rule_version": rule_version, "dedup_key": dedup_key}
        )
        if duplicate_group is None:
            logger.error(
                f"Failed to create duplicate group for request {request.id} with dedup key {dedup_key}"
            )
            return False
        logger.info(
            f"Duplicate group {duplicate_group.id} created for request {request.id} with dedup key {dedup_key}"
        )
        request.update(
            db=self.db, data={"duplicate_request_group_id": duplicate_group.id}
        )

        # if this is the only request in the group, it is not a duplicate
        if len(duplicates) == 0:
            return False

        if request.status == PrivacyRequestStatus.duplicate:
            logger.warning(
                f"Request {request.id} is a duplicate request that was requeued. This should not happen."
            )
            request.add_error_execution_log(
                db=self.db,
                connection_key=None,
                dataset_name="Duplicate Request Detection",
                collection_name=None,
                message=f"Request {request.id} is a duplicate request that was requeued. This should not happen.",
                action_type=ActionType.access,
            )
            return True

        # only compare to non-duplicate requests for the following cases
        canonical_requests = [
            request
            for request in duplicates
            if request.status != PrivacyRequestStatus.duplicate
        ]
        # If no non-duplicate requests are found, this request is not a duplicate.
        if len(canonical_requests) == 0:
            return False

        # If any requests in group are actioned, this request is a duplicate.
        actioned_in_group = [
            duplicate
            for duplicate in canonical_requests
            if duplicate.status in ACTIONED_REQUEST_STATUSES
        ]
        if len(actioned_in_group) > 0:
            logger.debug(
                f"Request {request.id} is a duplicate: it is duplicating actioned request(s) {actioned_in_group}."
            )
            return True
        # Check against verified identity rules.
        return self.verified_identity_cases(request, canonical_requests)
