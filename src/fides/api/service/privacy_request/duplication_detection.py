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

    def assign_duplicate_request_group_id(
        self, request: PrivacyRequest, duplicates: list[PrivacyRequest]
    ):
        print(f"duplicates: {[duplicate.id for duplicate in duplicates]}")
        print(f"request: {request.id}")
        group_ids = [
            duplicate.duplicate_request_group_id
            for duplicate in duplicates
            if duplicate.duplicate_request_group_id
        ]
        if len(group_ids) == 0:
            group_id = str(uuid4())
            for duplicate in duplicates:
                duplicate.update(
                    db=self.db, data={"duplicate_request_group_id": group_id}
                )
            request.update(db=self.db, data={"duplicate_request_group_id": group_id})
        if len(group_ids) == 1:
            request.update(
                db=self.db, data={"duplicate_request_group_id": group_ids[0]}
            )
        if len(group_ids) > 1:
            most_recent_request = max(duplicates, key=lambda x: x.updated_at)
            request.update(
                db=self.db,
                data={
                    "duplicate_request_group_id": most_recent_request.duplicate_request_group_id
                },
            )

        print(f"request group id: {request.duplicate_request_group_id}")
        print(
            f"group ids: {[duplicate.duplicate_request_group_id for duplicate in duplicates]}"
        )

    def actioned_request_cases(
        self, request: PrivacyRequest, duplicates: list[PrivacyRequest]
    ) -> bool:
        """
        Apply actioned request rules to determine if a request is the canonical request.
        If any existing requests are actioned, the new request is not the canonical request.

        Args:
            request: The privacy request to check
            duplicates: The list of duplicate requests

        Returns:
            True if the request is the canonical request, False otherwise
        """
        actioned_in_group = [
            duplicate
            for duplicate in duplicates
            if duplicate.status in ACTIONED_REQUEST_STATUSES
        ]
        if len(actioned_in_group) > 0:
            return False

    def verified_identity_cases(
        self, request: PrivacyRequest, duplicates: list[PrivacyRequest]
    ) -> bool:
        """
        Apply verified identity rules to determine if a request is the canonical request.
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
        print(f"verified in group: {[duplicate.id for duplicate in verified_in_group]}")
        if not request.identity_verified_at:
            if len(verified_in_group) > 0:  # other identities in group are verified
                return False
            if request.created_at < min(
                duplicate.created_at for duplicate in duplicates
            ):
                return True  # this was the first request to be created

        # if the request identitiy is verified and no duplicates are verified, it is the canonical request
        if request.identity_verified_at:
            if not verified_in_group:
                return True

            # if this is the first request to be verified, it is the canonical request
            if request.identity_verified_at < min(
                duplicate.identity_verified_at for duplicate in duplicates
            ):
                return True

    def is_canonical_request(
        self, request: PrivacyRequest, config: DuplicateDetectionSettings
    ) -> bool:
        """
        Determine if a request is the canonical request in a duplicate group.

        Args:
            request: The privacy request to check

        Returns:
            True if the request is the canonical request, False otherwise
        """
        canonical_status = None
        if request.status == PrivacyRequestStatus.duplicate:
            return False
        duplicates = self.find_duplicate_privacy_requests(request, config)
        self.assign_duplicate_request_group_id(request, duplicates)
        # if this is the only request in the group, it is the canonical request
        if len(duplicates) == 0:
            return True

        # only consider canonical requests for the following cases
        canonical_requests = [
            request
            for request in duplicates
            if request.status != PrivacyRequestStatus.duplicate
        ]
        if len(canonical_requests) == 0:
            logger.warning(
                f"No canonical requests found in group {request.duplicate_request_group_id}"
            )
            return True
        canonical_status = self.actioned_request_cases(request, canonical_requests)
        if canonical_status is not None:
            return canonical_status
        canonical_status = self.verified_identity_cases(request, canonical_requests)
        if canonical_status is not None:
            return canonical_status
        if canonical_status is None:
            logger.warning(
                f"No canonical status found for request {request.id} in group {request.duplicate_request_group_id}"
            )
