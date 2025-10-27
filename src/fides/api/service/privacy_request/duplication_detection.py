from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.privacy_request.privacy_request import PrivacyRequest
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
