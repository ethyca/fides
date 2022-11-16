from enum import Enum
from re import compile as regex
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Extra, root_validator

from fides.api.ops.models.privacy_request import CheckpointActionRequired
from fides.api.ops.schemas import Msg
from fides.api.ops.schemas.shared_schemas import FidesOpsKey


class MessagingMethod(Enum):
    """Enum for messaging method"""

    EMAIL = "email"
    SMS = "sms"


class MessagingServiceType(Enum):
    """Enum for messaging service type. Upper-cased in the database"""

    MAILGUN = "MAILGUN"

    TWILIO_TEXT = "TWILIO_TEXT"
    TWILIO_EMAIL = "TWILIO_EMAIL"


EMAIL_MESSAGING_SERVICES: Tuple[str, ...] = (
    MessagingServiceType.MAILGUN.value,
    MessagingServiceType.TWILIO_EMAIL.value,
)
SMS_MESSAGING_SERVICES: Tuple[str, ...] = (MessagingServiceType.TWILIO_TEXT.value,)


class MessagingActionType(str, Enum):
    """Enum for messaging action type"""

    # verify email upon acct creation
    CONSENT_REQUEST = "consent_request"
    SUBJECT_IDENTITY_VERIFICATION = "subject_identity_verification"
    MESSAGE_ERASURE_REQUEST_FULFILLMENT = "message_erasure_fulfillment"
    PRIVACY_REQUEST_ERROR_NOTIFICATION = "privacy_request_error_notification"
    PRIVACY_REQUEST_RECEIPT = "privacy_request_receipt"
    PRIVACY_REQUEST_COMPLETE_ACCESS = "privacy_request_complete_access"
    PRIVACY_REQUEST_COMPLETE_DELETION = "privacy_request_complete_deletion"
    PRIVACY_REQUEST_REVIEW_DENY = "privacy_request_review_deny"
    PRIVACY_REQUEST_REVIEW_APPROVE = "privacy_request_review_approve"


class ErrorNotificaitonBodyParams(BaseModel):
    """Body params required for privacy request error notifications."""

    unsent_errors: int


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


class EmailForActionType(BaseModel):
    """Email details that depend on action type"""

    subject: str
    body: str


class MessagingServiceDetails(Enum):
    """Enum for messaging service details"""

    # Mailgun
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

    # Mailgun
    MAILGUN_API_KEY = "mailgun_api_key"

    # Twilio SMS
    TWILIO_ACCOUNT_SID = "twilio_account_sid"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"
    TWILIO_MESSAGING_SERVICE_SID = "twilio_messaging_service_sid"
    TWILIO_SENDER_PHONE_NUMBER = "twilio_sender_phone_number"

    # Twilio Sendgrid/Email
    TWILIO_API_KEY = "twilio_api_key"


class MessagingServiceSecretsMailgun(BaseModel):
    """The secrets required to connect to mailgun."""

    mailgun_api_key: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class MessagingServiceSecretsTwilioSMS(BaseModel):
    """The secrets required to connect to twilio SMS."""

    twilio_account_sid: str
    twilio_auth_token: str
    twilio_messaging_service_sid: Optional[str]
    twilio_sender_phone_number: Optional[str]

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        sender_phone = values.get("twilio_sender_phone_number")
        if not values.get("twilio_messaging_service_sid") and not sender_phone:
            raise ValueError(
                "Either the twilio_messaging_service_sid or the twilio_sender_phone_number should be supplied."
            )
        if sender_phone:
            pattern = regex(r"^\+\d+$")
            if not pattern.search(sender_phone):
                raise ValueError(
                    "Sender phone number must include country code, formatted like +15558675309"
                )
        return values


class MessagingServiceSecretsTwilioEmail(BaseModel):
    """The secrets required to connect to twilio email."""

    twilio_api_key: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class MessagingConfigRequest(BaseModel):
    """Messaging Config Request Schema"""

    name: str
    key: Optional[FidesOpsKey]
    service_type: MessagingServiceType
    details: Optional[MessagingServiceDetailsMailgun]

    class Config:
        use_enum_values = False
        orm_mode = True

    @root_validator(pre=True)
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        service_type_pre = values.get("service_type")
        if service_type_pre:
            # uppercase to match enums in database
            values["service_type"] = service_type_pre.upper()
            service_type: MessagingServiceType = values["service_type"]
            if service_type == MessagingServiceType.MAILGUN.value:
                if not values.get("details"):
                    raise ValueError("Mailgun messaging config must include details")
        return values


class MessagingConfigResponse(BaseModel):
    """Messaging Config Response Schema"""

    name: str
    key: FidesOpsKey
    service_type: MessagingServiceType
    details: Optional[Dict[MessagingServiceDetails, Any]]

    class Config:
        orm_mode = True
        use_enum_values = True


SUPPORTED_MESSAGING_SERVICE_SECRETS = Union[
    MessagingServiceSecretsMailgun,
    MessagingServiceSecretsTwilioSMS,
    MessagingServiceSecretsTwilioEmail,
]


class MessagingConnectionTestStatus(Enum):
    """Enum for supplying statuses of validating credentials for a messaging Config"""

    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class TestMessagingStatusMessage(Msg):
    """A schema for checking status of message config."""

    test_status: Optional[MessagingConnectionTestStatus] = None
    failure_reason: Optional[str] = None
