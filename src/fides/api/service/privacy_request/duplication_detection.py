from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

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
from fides.config.config_proxy import ConfigProxy
from fides.config.duplicate_detection_settings import DuplicateDetectionSettings

ACTIONED_REQUEST_STATUSES = [
    PrivacyRequestStatus.approved,
    PrivacyRequestStatus.in_processing,
    PrivacyRequestStatus.requires_manual_finalization,
    PrivacyRequestStatus.requires_input,
    PrivacyRequestStatus.paused,
    PrivacyRequestStatus.awaiting_email_send,
    PrivacyRequestStatus.error,
]


class DuplicateDetectionService:
    def __init__(self, db: Session):
        self.db = db
        self._config = ConfigProxy(db).privacy_request_duplicate_detection

    def is_enabled(self) -> bool:
        return self._config.enabled

    def _create_identity_conditions(
        self, current_request: PrivacyRequest
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
            if pi.field_name in self._config.match_identity_fields
        }
        if len(current_identities) != len(self._config.match_identity_fields):
            missing_fields = [
                field
                for field in self._config.match_identity_fields
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
    ) -> Optional[ConditionGroup]:
        """
        Create conditions for duplicate detection based on configuration.

        Args:
            current_request: The current privacy request to find duplicates for
            config: Duplicate detection configuration settings

        Returns:
            A ConditionGroup with AND operator, or None if no conditions can be created
        """
        if len(self._config.match_identity_fields) == 0:
            return None

        identity_conditions = self._create_identity_conditions(current_request)
        if not identity_conditions:
            return None  # Only proceed if we have identity conditions

        time_window_condition = self._create_time_window_condition(
            self._config.time_window_days
        )

        # Combine all conditions with AND operator
        all_conditions: list[Condition] = [*identity_conditions, time_window_condition]
        return ConditionGroup(
            logical_operator=GroupOperator.and_, conditions=all_conditions
        )

    def find_duplicate_privacy_requests(
        self,
        current_request: PrivacyRequest,
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
        condition = self.create_duplicate_detection_conditions(current_request)

        if condition is None:
            return []

        translator = SQLConditionTranslator(self.db)
        query = translator.generate_query_from_condition(condition)

        query = query.filter(PrivacyRequest.id != current_request.id).filter(
            PrivacyRequest.deleted_at.is_(None)
        )
        return query.all()

    def generate_dedup_key(self, request: PrivacyRequest) -> str:
        """
        Generate a dedup key for a request based on the duplicate detection settings.
        """
        current_identities: dict[str, str] = {
            pi.field_name: pi.hashed_value
            for pi in request.provided_identities  # type: ignore [attr-defined]
            if pi.field_name in self._config.match_identity_fields
        }
        if len(current_identities) != len(self._config.match_identity_fields):
            raise ValueError(
                "This request does not contain the required identity fields for duplicate detection."
            )
        return "|".join(
            [
                current_identities[field]
                for field in sorted(self._config.match_identity_fields)
            ]
        )

    def update_duplicate_group_ids(
        self,
        request: PrivacyRequest,
        duplicates: list[PrivacyRequest],
        duplicate_group_id: UUID,
    ) -> None:
        """
        Update the duplicate request group ids for a request and its duplicates.
        Args:
            request: The privacy request to update
            duplicates: The list of duplicate requests to update
            duplicate_group_id: The duplicate request group id to update
        """
        update_all = [request] + duplicates
        try:
            for privacy_request in update_all:
                privacy_request.duplicate_request_group_id = duplicate_group_id  # type: ignore [assignment]
        except Exception as e:
            logger.error(f"Failed to update duplicate request group ids: {e}")
            raise e

    def mark_as_duplicate(self, request: PrivacyRequest, message: str) -> None:
        """
        Mark a request as a duplicate.
        """
        request.update(self.db, data={"status": PrivacyRequestStatus.duplicate})
        logger.debug(message)
        self.add_error_execution_log(request, message)

    def add_error_execution_log(self, request: PrivacyRequest, message: str) -> None:
        request.add_error_execution_log(
            db=self.db,
            connection_key=None,
            dataset_name="Duplicate Request Detection",
            collection_name=None,
            message=message,
            action_type=(
                request.policy.get_action_type()  # type: ignore [arg-type]
                if request.policy
                else ActionType.access
            ),
        )

    def add_success_execution_log(self, request: PrivacyRequest, message: str) -> None:
        request.add_success_execution_log(
            db=self.db,
            connection_key=None,
            dataset_name="Duplicate Request Detection",
            collection_name=None,
            message=message,
            action_type=(
                request.policy.get_action_type()  # type: ignore [arg-type]
                if request.policy
                else ActionType.access
            ),
        )

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
                message = f"Request {request.id} is a duplicate: it is duplicating request(s) {[duplicate.id for duplicate in verified_in_group]}."
                self.mark_as_duplicate(request, message)
                return True

            canonical_request = min(duplicates, key=lambda x: x.created_at)  # type: ignore [arg-type, return-value]
            canonical_request_created_at = canonical_request.created_at or datetime.now(
                timezone.utc
            )
            request_created_at = request.created_at or datetime.now(timezone.utc)
            if request_created_at < canonical_request_created_at:
                message = f"Request {request.id} is not a duplicate: it is the first request to be created in the group."
                logger.debug(message)
                self.add_success_execution_log(request, message)
                return False

            message = f"Request {request.id} is a duplicate: it is duplicating request(s) ['{canonical_request.id}']."
            self.mark_as_duplicate(request, message)
            return True

        # The request identity is verified.
        if not verified_in_group:
            message = f"Request {request.id} is not a duplicate: it is the first request to be verified in the group."
            logger.debug(message)
            for duplicate in duplicates:
                dup_message = f"Request {duplicate.id} is a duplicate: it is duplicating request(s) ['{request.id}']."
                self.mark_as_duplicate(duplicate, dup_message)
            self.add_success_execution_log(request, message)
            return False

        # If this request is the first with a verified identity, it is not a duplicate.
        canonical_request = min(verified_in_group, key=lambda x: x.identity_verified_at)  # type: ignore [arg-type, return-value]
        canonical_request_verified_at = (
            canonical_request.identity_verified_at or datetime.now(timezone.utc)
        )
        request_verified_at = request.identity_verified_at or datetime.now(timezone.utc)
        if request_verified_at < canonical_request_verified_at:
            message = f"Request {request.id} is not a duplicate: it is the first request to be verified in the group."
            logger.debug(message)
            self.add_success_execution_log(request, message)
            for duplicate in duplicates:
                dup_message = f"Request {duplicate.id} is a duplicate: it is duplicating request(s) ['{request.id}']."
                self.mark_as_duplicate(duplicate, dup_message)
            return False
        message = f"Request {request.id} is a duplicate: it is duplicating request(s) ['{canonical_request.id}']."
        self.mark_as_duplicate(request, message)
        return True

    # pylint: disable=too-many-return-statements
    def is_duplicate_request(self, request: PrivacyRequest) -> bool:
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
        if request.policy.get_action_type() == ActionType.consent:
            message = f"Consent request {request.id} is not a duplicate."
            logger.info(message)
            self.add_success_execution_log(request, message)
            return False
        duplicates = self.find_duplicate_privacy_requests(request)
        rule_version = generate_rule_version(
            DuplicateDetectionSettings(
                enabled=self._config.enabled,
                time_window_days=self._config.time_window_days,
                match_identity_fields=self._config.match_identity_fields,
            )
        )
        try:
            dedup_key = self.generate_dedup_key(request)
        except ValueError as e:
            message = f"Request {request.id} is not a duplicate: {e}"
            logger.warning(message)
            self.add_success_execution_log(request, message)
            return False

        _, duplicate_group = DuplicateGroup.get_or_create(
            db=self.db, data={"rule_version": rule_version, "dedup_key": dedup_key}
        )
        if duplicate_group is None:
            message = f"Failed to create duplicate group for request {request.id} with dedup key {dedup_key}"
            logger.error(message)
            self.add_error_execution_log(request, message)
            return False

        self.update_duplicate_group_ids(request, duplicates, duplicate_group.id)  # type: ignore [arg-type]

        if request.status in ACTIONED_REQUEST_STATUSES:
            message = (
                f"Request {request.id} is not a duplicate: it is an actioned request."
            )
            logger.debug(message)
            self.add_success_execution_log(request, message)
            return False

        # if this is the only request in the group, it is not a duplicate
        if len(duplicates) == 0:
            message = f"Request {request.id} is not a duplicate."
            logger.debug(message)
            self.add_success_execution_log(request, message)
            return False

        if request.status == PrivacyRequestStatus.duplicate:
            return True

        # only compare to non-duplicate/complete requests for the following cases
        canonical_requests = [
            duplicate
            for duplicate in duplicates
            if duplicate.status
            not in [PrivacyRequestStatus.duplicate, PrivacyRequestStatus.complete]
        ]
        # If no non-duplicate requests are found, this request is not a duplicate.
        if len(canonical_requests) == 0:
            message = f"Request {request.id} is not a duplicate."
            logger.debug(message)
            self.add_success_execution_log(request, message)
            return False

        # If any requests in group are actioned, this request is a duplicate.
        actioned_in_group = [
            duplicate
            for duplicate in canonical_requests
            if duplicate.status in ACTIONED_REQUEST_STATUSES
        ]
        if len(actioned_in_group) > 0:
            message = f"Request {request.id} is a duplicate: it is duplicating actioned request(s) {[duplicate.id for duplicate in actioned_in_group]}."
            self.mark_as_duplicate(request, message)
            return True
        # Check against verified identity rules.
        return self.verified_identity_cases(request, canonical_requests)


def check_for_duplicates(db: Session, privacy_request: PrivacyRequest) -> None:
    duplicate_detection_service = DuplicateDetectionService(db)
    if duplicate_detection_service.is_enabled():
        logger.info(
            "Duplicate detection is enabled. Checking if privacy request is a duplicate."
        )
        if duplicate_detection_service.is_duplicate_request(privacy_request):
            logger.info("Terminating privacy request: request is a duplicate.")
