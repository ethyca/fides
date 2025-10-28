from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.privacy_request.privacy_request import PrivacyRequest
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
from fides.config.duplicate_detection_settings import DuplicateDetectionSettings

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
        self, current_request: PrivacyRequest, config: DuplicateDetectionSettings
    ) -> list[Condition]:
        """Creates conditions for matching identity fields.

        For identity field matching using the EAV pattern in ProvidedIdentity,
        we need to match both field_name and hashed_value. This function
        creates the required nested conditions for each identity field.

        Also adds a condition for the policy_id to ensure that we are only matching requests for the same policy.
        """
        current_identities: dict[str, str] = {}
        conditions: list[Condition] = []
        current_identities = {
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
        config: DuplicateDetectionSettings,
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
        config: DuplicateDetectionSettings,
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
        # Create conditions from config
        condition = self.create_duplicate_detection_conditions(current_request, config)

        if condition is None:
            return []

        translator = SQLConditionTranslator(self.db)
        query = translator.generate_query_from_condition(condition)

        query = query.filter(PrivacyRequest.id != current_request.id)
        return query.all()

    def get_duplicate_request_group_id(self, duplicates: list[PrivacyRequest]) -> str:
        """
        Get the duplicate request group id for a list of requests.
        Ideally there will only be one group id, but if there are multiple, we return the most recent group id.
        """
        duplicate_group_ids: set[str] = {
            duplicate.duplicate_request_group_id
            for duplicate in duplicates
            if duplicate.duplicate_request_group_id is not None
        }
        if len(duplicate_group_ids) == 0:
            return str(uuid4())
        if len(duplicate_group_ids) == 1:
            return duplicate_group_ids.pop()
        logger.warning(
            f"Multiple duplicate request group ids found for requests: {duplicates}"
        )
        # return the most recent group id.
        ordered_group_ids = [
            (duplicate.duplicate_request_group_id, duplicate.created_at)
            for duplicate in duplicates
            if duplicate.duplicate_request_group_id is not None
            and duplicate.created_at is not None
        ]
        ordered_group_ids.sort(key=lambda x: x[1], reverse=True)
        return ordered_group_ids[0][0]

    def verified_identity_cases(
        self, request: PrivacyRequest, duplicates: list[PrivacyRequest]
    ) -> bool:
        """
        Apply verified identity rules to determine if a request is the canonical request.
        - If this request does not have a verified identity, it may be canonical if no other requests in group are verified.
        - If this is the first request to be verified, it is the canonical request
        - If other requests identities that were verified before this request, it is not the canonical request
        Args:
            request: The privacy request to check
            duplicates: The list of duplicate requests

        Returns:
            True if the request is the canonical request, False otherwise
        """
        verified_in_group = [
            duplicate for duplicate in duplicates if duplicate.identity_verified_at
        ]

        ### The request identity is not verified.
        if not request.identity_verified_at:
            # If other requests in group are verified, this request is not canonical.
            if len(verified_in_group) > 0:
                return False
            # If this is the first request to be created, it is the canonical request.
            min_created_at = min(
                (d.created_at for d in duplicates if d.created_at), default=None
            ) or datetime.now(timezone.utc)
            request_created_at = (
                request.created_at
                if request.created_at is not None
                else datetime.now(timezone.utc)
            )
            if request_created_at < min_created_at:
                return True
            # This request is not the first request to be created or first verified.
            return False

        ### The request identity is verified.
        if not verified_in_group:
            # No other requests in group are verified.
            return True

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
            return True  # This request is the first with verified identity.
        return False

    def is_canonical_request(
        self, request: PrivacyRequest, config: DuplicateDetectionSettings
    ) -> bool:
        """
        Determine if a request is the canonical request in a duplicate group.

        The hierarchy is:
        - Actioned requests: if this request duplicates and actioned request, it is not canonical.
        - Verified identity requests:
          - if this request has a verified identity:
            - If none of the duplicates have a verified identity, it is canonical.
            - If duplicates have verified identities, but this request is the first with a verified identity, it is canonical.
          - if this request does not have a verified identity:
            - If no duplicates have a verified identity, and this was the first created request, it is canonical.
        - First created request: if this is the first created request in the group, it is canonical.
        - If no canonical requests are found (meaning all requests are marked as duplicates), this request is canonical.

        Args:
            request: The privacy request to check

        Returns:
            True if the request is the canonical request, False otherwise
        """
        duplicates = self.find_duplicate_privacy_requests(request, config)
        group_id = self.get_duplicate_request_group_id(duplicates)
        request.update(db=self.db, data={"duplicate_request_group_id": group_id})

        if request.status == PrivacyRequestStatus.duplicate:
            return False
        # if this is the only request in the group, it is the canonical request
        if len(duplicates) == 0:
            return True

        # only consider canonical requests for the following cases
        canonical_requests = [
            request
            for request in duplicates
            if request.status != PrivacyRequestStatus.duplicate
        ]
        # If no canonical requests are found, this request is the canonical request.
        if len(canonical_requests) == 0:
            return True

        # If any requests in group are actioned, this request is not canonical.
        actioned_in_group = [
            duplicate
            for duplicate in duplicates
            if duplicate.status in ACTIONED_REQUEST_STATUSES
        ]
        if len(actioned_in_group) > 0:
            return False

        # Check against verified identity rules.
        return self.verified_identity_cases(request, canonical_requests)
