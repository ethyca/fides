from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Extra

from fides.api.ops.models.privacy_request import CheckpointActionRequired
from fides.api.ops.schemas import Msg
from fides.api.ops.schemas.shared_schemas import FidesOpsKey


class MessagingMethod(Enum):
    """Enum for messaging method"""

    EMAIL = "email"
    SMS = "sms"


class MessagingServiceType(Enum):
    """Enum for messaging service type"""

    MAILGUN = "mailgun"

    TWILIO_TEXT = "twilio_text"
    TWILIO_EMAIL = "twilio_email"

    def get_messaging_method(self) -> Optional[MessagingMethod]:
        """returns messaging method based on configured service type"""
        if self in EMAIL_MESSAGING_SERVICES:
            return MessagingMethod.EMAIL
        if self in SMS_MESSAGING_SERVICES:
            return MessagingMethod.SMS
        return None


EMAIL_MESSAGING_SERVICES = [
    MessagingServiceType.MAILGUN,
    MessagingServiceType.TWILIO_EMAIL,
]
SMS_MESSAGING_SERVICES = [MessagingServiceType.TWILIO_TEXT]


class MessagingActionType(str, Enum):
    """Enum for messaging action type"""

    # verify email upon acct creation
    CONSENT_REQUEST = "consent_request"
    SUBJECT_IDENTITY_VERIFICATION = "subject_identity_verification"
    MESSAGE_ERASURE_REQUEST_FULFILLMENT = "message_erasure_fulfillment"
    PRIVACY_REQUEST_RECEIPT = "privacy_request_receipt"
    PRIVACY_REQUEST_COMPLETE_ACCESS = "privacy_request_complete_access"
    PRIVACY_REQUEST_COMPLETE_DELETION = "privacy_request_complete_deletion"
    PRIVACY_REQUEST_REVIEW_DENY = "privacy_request_review_deny"
    PRIVACY_REQUEST_REVIEW_APPROVE = "privacy_request_review_approve"


class SubjectIdentityVerificationBodyParams(BaseModel):
    """Body params required for subject identity verification email/sms template"""

    verification_code: str
    verification_code_ttl_seconds: int

    def get_verification_code_ttl_minutes(self) -> int:
        """returns verification_code_ttl_seconds in minutes"""
        if self.verification_code_ttl_seconds < 60:
            return 0
        return self.verification_code_ttl_seconds // 60


class RequestReceiptBodyParams(BaseModel):
    """Body params required for privacy request receipt template"""

    request_types: List[str]


class AccessRequestCompleteBodyParams(BaseModel):
    """Body params required for privacy request completion access template"""

    download_links: List[str]


class RequestReviewDenyBodyParams(BaseModel):
    """Body params required for privacy request review deny template"""

    rejection_reason: Optional[str]


class FidesopsMessage(
    BaseModel,
    smart_union=True,
    arbitrary_types_allowed=True,
):
    """A mapping of action_type to body_params"""

    action_type: MessagingActionType
    body_params: Optional[
        Union[
            SubjectIdentityVerificationBodyParams,
            RequestReceiptBodyParams,
            RequestReviewDenyBodyParams,
            AccessRequestCompleteBodyParams,
            List[CheckpointActionRequired],
        ]
    ]


class MessageForActionType(BaseModel):
    """Message details that depend on action type"""

    subject: str
    body: str


class MessagingServiceDetails(Enum):
    """Enum for messaging service details"""

    # mailgun-specific
    IS_EU_DOMAIN = "is_eu_domain"
    API_VERSION = "api_version"
    DOMAIN = "domain"


class MessagingServiceDetailsMailgun(BaseModel):
    """The details required to represent a Mailgun email configuration."""

    is_eu_domain: Optional[bool] = False
    api_version: Optional[str] = "v3"
    domain: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class MessagingServiceSecrets(Enum):
    """Enum for message service secrets"""

    # mailgun-specific
    MAILGUN_API_KEY = "mailgun_api_key"

    # twilio
    TWILIO_ACCOUNT_SID = "twilio_account_sid"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"
    TWILIO_MESSAGING_SERVICE_ID = "twilio_messaging_service_id"


class MessagingServiceSecretsMailgun(BaseModel):
    """The secrets required to connect to mailgun."""

    mailgun_api_key: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class MessagingServiceSecretsTwilio(BaseModel):
    """The secrets required to connect to twilio email."""

    account_sid: str
    auth_token: str
    messaging_service_id: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class MessagingConfigRequest(BaseModel):
    """Messaging Config Request Schema"""

    name: str
    key: Optional[FidesOpsKey]
    service_type: MessagingServiceType
    details: Union[MessagingServiceDetailsMailgun]

    class Config:
        use_enum_values = False
        orm_mode = True


class MessagingConfigResponse(BaseModel):
    """Messaging Config Response Schema"""

    name: str
    key: FidesOpsKey
    service_type: MessagingServiceType
    details: Dict[MessagingServiceDetails, Any]

    class Config:
        orm_mode = True
        use_enum_values = True


SUPPORTED_MESSAGING_SERVICE_SECRETS = Union[
    MessagingServiceSecretsMailgun, MessagingServiceSecretsTwilio
]


class MessagingConnectionTestStatus(Enum):
    """Enum for supplying statuses of validating credentials for an Messaging Config"""

    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class TestMessagingStatusMessage(Msg):
    """A schema for checking status of message config."""

    test_status: Optional[MessagingConnectionTestStatus] = None
    failure_reason: Optional[str] = None
