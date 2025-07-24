import secrets
from typing import Optional, Set, Union

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    IdentityNotFoundException,
    PolicyNotFoundException,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    ConsentRequest,
    PrivacyRequest,
    PrivacyRequestError,
    PrivacyRequestNotifications,
    ProvidedIdentityType,
)
from fides.api.schemas.messaging.messaging import (
    EMAIL_MESSAGING_SERVICES,
    ErrorNotificationBodyParams,
    FidesopsMessage,
    MessagingActionType,
    RequestReceiptBodyParams,
    RequestReviewDenyBodyParams,
    SubjectIdentityVerificationBodyParams,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import (
    EMAIL_JOIN_STRING,
    dispatch_message,
    dispatch_message_task,
    message_send_enabled,
)
from fides.api.tasks import MESSAGING_QUEUE_NAME
from fides.config import FidesConfig, get_config
from fides.config.config_proxy import ConfigProxy


class MessagingService:
    def __init__(self, db: Session, config: FidesConfig, config_proxy: ConfigProxy):
        self.db = db
        self.config = config
        self.config_proxy = config_proxy

    def send_request_approved(self, privacy_request: PrivacyRequest) -> None:
        if message_send_enabled(
            self.db,
            privacy_request.property_id,
            MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE,
            self.config_proxy.notifications.send_request_review_notification,
        ):
            identity_data = privacy_request.get_cached_identity_data()
            if not identity_data:
                logger.error(
                    IdentityNotFoundException(
                        "Identity was not found, so request review message could not be sent."
                    )
                )
                return

            to_identity = Identity(
                email=identity_data.get(ProvidedIdentityType.email.value),
                phone_number=identity_data.get(ProvidedIdentityType.phone_number.value),
            )

            dispatch_message_task.apply_async(
                queue=MESSAGING_QUEUE_NAME,
                kwargs={
                    "message_meta": FidesopsMessage(
                        action_type=MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE,
                        body_params=None,
                    ).model_dump(mode="json"),
                    "service_type": self.config_proxy.notifications.notification_service_type,
                    "to_identity": to_identity.model_dump(mode="json"),
                    "property_id": privacy_request.property_id,
                },
            )

    def send_request_denied(
        self, privacy_request: PrivacyRequest, deny_reason: Optional[str] = None
    ) -> None:
        if message_send_enabled(
            self.db,
            privacy_request.property_id,
            MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY,
            self.config_proxy.notifications.send_request_review_notification,
        ):
            identity_data = privacy_request.get_cached_identity_data()
            if not identity_data:
                logger.error(
                    IdentityNotFoundException(
                        "Identity was not found, so request review message could not be sent."
                    )
                )
                return

            to_identity = Identity(
                email=identity_data.get(ProvidedIdentityType.email.value),
                phone_number=identity_data.get(ProvidedIdentityType.phone_number.value),
            )

            dispatch_message_task.apply_async(
                queue=MESSAGING_QUEUE_NAME,
                kwargs={
                    "message_meta": FidesopsMessage(
                        action_type=MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY,
                        body_params=RequestReviewDenyBodyParams(
                            rejection_reason=deny_reason
                        ),
                    ).model_dump(mode="json"),
                    "service_type": self.config_proxy.notifications.notification_service_type,
                    "to_identity": to_identity.model_dump(mode="json"),
                    "property_id": privacy_request.property_id,
                },
            )

    def send_verification_code(
        self,
        request: Union[ConsentRequest, PrivacyRequest],
        to_identity: Optional[Identity],
        property_id: Optional[str],
    ) -> Optional[str]:

        verification_code = None

        if message_send_enabled(
            self.db,
            request.property_id,
            MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
            self.config_proxy.execution.subject_identity_verification_required,
        ):
            verification_code = _generate_id_verification_code()
            request.cache_identity_verification_code(verification_code)

            dispatch_message(
                self.db,
                action_type=MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                to_identity=to_identity,
                service_type=self.config_proxy.notifications.notification_service_type,
                message_body_params=SubjectIdentityVerificationBodyParams(
                    verification_code=verification_code,
                    verification_code_ttl_seconds=self.config.redis.identity_verification_code_ttl_seconds,
                ),
                property_id=property_id,
            )

        return verification_code

    def send_privacy_request_receipt(
        self,
        policy: Optional[Policy],
        identity: Identity,
        privacy_request: PrivacyRequest,
    ) -> None:
        if message_send_enabled(
            self.db,
            privacy_request.property_id,
            MessagingActionType.PRIVACY_REQUEST_RECEIPT,
            self.config_proxy.notifications.send_request_receipt_notification,
        ):
            if not identity:
                logger.error(
                    IdentityNotFoundException(
                        "Identity was not found, so request receipt message could not be sent."
                    )
                )
                return

            if not policy:
                logger.error(
                    PolicyNotFoundException(
                        "Policy was not found, so request receipt message could not be sent."
                    )
                )
                return

            request_types: Set[str] = set()
            for action_type in ActionType:
                if policy.get_rules_for_action(action_type=ActionType(action_type)):
                    request_types.add(action_type)

            request_types_list = list(request_types)

            dispatch_message_task.apply_async(
                queue=MESSAGING_QUEUE_NAME,
                kwargs={
                    "message_meta": FidesopsMessage(
                        action_type=MessagingActionType.PRIVACY_REQUEST_RECEIPT,
                        body_params=RequestReceiptBodyParams(
                            request_types=request_types_list
                        ),
                    ).model_dump(mode="json"),
                    "service_type": self.config.notifications.notification_service_type,
                    "to_identity": identity.labeled_dict(),
                    "property_id": privacy_request.property_id,
                },
            )


def _generate_id_verification_code() -> str:
    """
    Generate one-time identity verification code
    """
    return str(secrets.choice(range(100000, 999999)))


def check_and_dispatch_error_notifications(db: Session) -> None:
    config_proxy = ConfigProxy(db)
    privacy_request_notifications = PrivacyRequestNotifications.all(db=db)
    if not privacy_request_notifications:
        return None

    unsent_errors = PrivacyRequestError.filter(
        db=db, conditions=(PrivacyRequestError.message_sent.is_(False))
    ).all()
    if not unsent_errors:
        return None

    email_config = (
        config_proxy.notifications.notification_service_type in EMAIL_MESSAGING_SERVICES
    )

    if (
        email_config
        and len(unsent_errors) >= privacy_request_notifications[0].notify_after_failures
    ):
        for email in privacy_request_notifications[0].email.split(EMAIL_JOIN_STRING):
            dispatch_message_task.apply_async(
                queue=MESSAGING_QUEUE_NAME,
                kwargs={
                    "message_meta": FidesopsMessage(
                        action_type=MessagingActionType.PRIVACY_REQUEST_ERROR_NOTIFICATION,
                        body_params=ErrorNotificationBodyParams(
                            unsent_errors=len(unsent_errors)
                        ),
                    ).model_dump(mode="json"),
                    "service_type": config_proxy.notifications.notification_service_type,
                    "to_identity": {"email": email},
                    "property_id": None,
                },
            )

        for error in unsent_errors:
            error.update(db=db, data={"message_sent": True})

    return None


def send_verification_code_to_user(
    db: Session,
    request: Union[ConsentRequest, PrivacyRequest],
    to_identity: Optional[Identity],
    property_id: Optional[str],
) -> str:
    """Generate and cache a verification code, and then message the user"""
    config = get_config()
    config_proxy = ConfigProxy(db)
    verification_code = _generate_id_verification_code()
    request.cache_identity_verification_code(verification_code)
    messaging_action_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION
    dispatch_message(
        db,
        action_type=messaging_action_type,
        to_identity=to_identity,
        service_type=config_proxy.notifications.notification_service_type,
        message_body_params=SubjectIdentityVerificationBodyParams(
            verification_code=verification_code,
            verification_code_ttl_seconds=config.redis.identity_verification_code_ttl_seconds,
        ),
        property_id=property_id,
    )

    return verification_code


def send_privacy_request_receipt_message_to_user(
    policy: Optional[Policy],
    to_identity: Optional[Identity],
    service_type: Optional[str],
    property_id: Optional[str],
) -> None:
    """Helper function to send request receipt message to the user"""
    if not to_identity:
        logger.error(
            IdentityNotFoundException(
                "Identity was not found, so request receipt message could not be sent."
            )
        )
        return
    if not policy:
        logger.error(
            PolicyNotFoundException(
                "Policy was not found, so request receipt message could not be sent."
            )
        )
        return
    request_types: Set[str] = set()
    for action_type in ActionType:
        if policy.get_rules_for_action(action_type=ActionType(action_type)):
            request_types.add(action_type)

    request_types_list = list(request_types)

    dispatch_message_task.apply_async(
        queue=MESSAGING_QUEUE_NAME,
        kwargs={
            "message_meta": FidesopsMessage(
                action_type=MessagingActionType.PRIVACY_REQUEST_RECEIPT,
                body_params=RequestReceiptBodyParams(request_types=request_types_list),
            ).model_dump(mode="json"),
            "service_type": service_type,
            "to_identity": to_identity.labeled_dict(),
            "property_id": property_id,
        },
    )
