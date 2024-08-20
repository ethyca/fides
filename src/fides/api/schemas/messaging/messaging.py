from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from fideslang.default_taxonomy import DEFAULT_TAXONOMY
from fideslang.validation import FidesKey
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fides.api.custom_types import PhoneNumber, SafeStr
from fides.api.schemas import Msg
from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.privacy_preference import MinimalPrivacyPreferenceHistorySchema
from fides.api.schemas.privacy_request import Consent
from fides.api.schemas.property import MinimalProperty


class MessagingMethod(Enum):
    """Enum for messaging method"""

    EMAIL = "email"
    SMS = "sms"


class MessagingServiceType(Enum):
    """Enum for messaging service type. Upper-cased in the database"""

    mailgun = "mailgun"
    twilio_text = "twilio_text"
    twilio_email = "twilio_email"
    mailchimp_transactional = "mailchimp_transactional"

    @classmethod
    def _missing_(
        cls: Type[MessagingServiceType], value: Any
    ) -> Optional[MessagingServiceType]:
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return None


EMAIL_MESSAGING_SERVICES: Tuple[str, ...] = (
    MessagingServiceType.mailgun.value,
    MessagingServiceType.twilio_email.value,
    MessagingServiceType.mailchimp_transactional.value,
)
SMS_MESSAGING_SERVICES: Tuple[str, ...] = (MessagingServiceType.twilio_text.value,)


class MessagingActionType(str, Enum):
    """Enum for messaging action type"""

    # verify email upon acct creation
    CONSENT_REQUEST = "consent_request"
    SUBJECT_IDENTITY_VERIFICATION = "subject_identity_verification"
    CONSENT_REQUEST_EMAIL_FULFILLMENT = "consent_request_email_fulfillment"
    MESSAGE_ERASURE_REQUEST_FULFILLMENT = "message_erasure_fulfillment"
    PRIVACY_REQUEST_ERROR_NOTIFICATION = "privacy_request_error_notification"
    PRIVACY_REQUEST_RECEIPT = "privacy_request_receipt"
    PRIVACY_REQUEST_COMPLETE_ACCESS = "privacy_request_complete_access"
    PRIVACY_REQUEST_COMPLETE_DELETION = "privacy_request_complete_deletion"
    PRIVACY_REQUEST_REVIEW_DENY = "privacy_request_review_deny"
    PRIVACY_REQUEST_REVIEW_APPROVE = "privacy_request_review_approve"
    USER_INVITE = "user_invite"
    TEST_MESSAGE = "test_message"


CONFIGURABLE_MESSAGING_ACTION_TYPES: Tuple[str, ...] = (
    # These messaging action types are configurable in Admin-UI, and thus are the only templates that apply to the
    # property-specific messaging feature. The other action types as associated with hard-coded templates in Fides.
    MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value,
    MessagingActionType.PRIVACY_REQUEST_RECEIPT.value,
    MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS.value,
    MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION.value,
    MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY.value,
    MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE.value,
)


class ErrorNotificationBodyParams(BaseModel):
    """Body params required for privacy request error notifications."""

    unsent_errors: int


class SubjectIdentityVerificationBodyParams(BaseModel):
    """Body params required for subject identity verification email/sms template"""

    verification_code: SafeStr
    verification_code_ttl_seconds: int

    def get_verification_code_ttl_minutes(self) -> int:
        """returns verification_code_ttl_seconds in minutes"""
        if self.verification_code_ttl_seconds < 60:
            return 0
        return self.verification_code_ttl_seconds // 60


class RequestReceiptBodyParams(BaseModel):
    """Body params required for privacy request receipt template"""

    request_types: List[SafeStr]


class AccessRequestCompleteBodyParams(BaseModel):
    """Body params required for privacy request completion access template"""

    download_links: List[str]
    subject_request_download_time_in_days: int


class RequestReviewDenyBodyParams(BaseModel):
    """Body params required for privacy request review deny template"""

    rejection_reason: Optional[SafeStr] = None


class ConsentPreferencesByUser(BaseModel):
    """Used for capturing the preferences of a single user.

    Used for ConsentEmailFulfillmentBodyParams where we potentially send a list
    of batched user preferences to a third party vendor all at once.
    """

    identities: Dict[str, Any]
    consent_preferences: List[
        Consent
    ]  # Consent schema for old workflow # TODO Slated for deprecation
    privacy_preferences: List[
        MinimalPrivacyPreferenceHistorySchema
    ]  # Privacy preferences for new workflow

    @model_validator(mode="before")
    @classmethod
    def transform_data_use_format(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a data use fides_key to a corresponding name if possible"""
        consent_preferences = values.get("consent_preferences") or []
        for preference in consent_preferences:
            preference.data_use = next(
                (
                    data_use.name
                    for data_use in DEFAULT_TAXONOMY.data_use  # pylint:disable=not-an-iterable
                    or []
                    if data_use.fides_key == preference.data_use
                ),
                preference.data_use,
            )
        values["consent_preferences"] = consent_preferences
        return values


class ConsentEmailFulfillmentBodyParams(BaseModel):
    """Body params required to send batched user consent preferences by email"""

    controller: str
    third_party_vendor_name: str
    required_identities: List[str]
    requested_changes: List[ConsentPreferencesByUser]


class ErasureRequestBodyParams(BaseModel):
    """Body params required to send batched user erasure requests by email"""

    controller: str
    third_party_vendor_name: str
    identities: List[str]


class UserInviteBodyParams(BaseModel):
    """Body params required to send a user invite email"""

    username: str
    invite_code: str


class FidesopsMessage(
    BaseModel,
):
    """A mapping of action_type to body_params"""

    action_type: MessagingActionType
    body_params: Optional[
        Union[
            ConsentEmailFulfillmentBodyParams,
            SubjectIdentityVerificationBodyParams,
            RequestReceiptBodyParams,
            RequestReviewDenyBodyParams,
            AccessRequestCompleteBodyParams,
            ErasureRequestBodyParams,
            ErrorNotificationBodyParams,
            UserInviteBodyParams,
        ]
    ] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class EmailForActionType(BaseModel):
    """
    Represents email details for a specific action type, including subject and body.
    Template variables may be included if provided for the given action type and can be
    used by the downstream mailing service to customize messages, if supported.
    """

    subject: str
    body: str
    template_variables: Optional[Dict[str, Any]] = {}


class MessagingServiceDetails(Enum):
    """Enum for messaging service details"""

    # Generic
    DOMAIN = "domain"
    EMAIL_FROM = "email_from"

    # Mailgun
    IS_EU_DOMAIN = "is_eu_domain"
    API_VERSION = "api_version"

    # Twilio Email
    TWILIO_EMAIL_FROM = "twilio_email_from"


class MessagingServiceDetailsMailchimpTransactional(BaseModel):
    """The details required to represent a Mailchimp Transactional email configuration."""

    email_from: str
    model_config = ConfigDict(extra="forbid")


class MessagingServiceDetailsMailgun(BaseModel):
    """The details required to represent a Mailgun email configuration."""

    is_eu_domain: Optional[bool] = False
    api_version: Optional[str] = "v3"
    domain: str
    model_config = ConfigDict(extra="forbid")


class MessagingServiceDetailsTwilioEmail(BaseModel):
    """The details required to represent a Twilio email configuration."""

    twilio_email_from: str
    model_config = ConfigDict(extra="forbid")


class MessagingServiceSecrets(Enum):
    """Enum for message service secrets"""

    # Mailchimp Transactional
    MAILCHIMP_TRANSACTIONAL_API_KEY = "mailchimp_transactional_api_key"

    # Mailgun
    MAILGUN_API_KEY = "mailgun_api_key"

    # Twilio SMS
    TWILIO_ACCOUNT_SID = "twilio_account_sid"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"
    TWILIO_MESSAGING_SERVICE_SID = "twilio_messaging_service_sid"
    TWILIO_SENDER_PHONE_NUMBER = "twilio_sender_phone_number"

    # Twilio Sendgrid/Email
    TWILIO_API_KEY = "twilio_api_key"


class MessagingServiceSecretsMailchimpTransactional(BaseModel):
    """The secrets required to connect to Mailchimp Transactional."""

    mailchimp_transactional_api_key: str
    model_config = ConfigDict(extra="forbid")


class MessagingServiceSecretsMailgun(BaseModel):
    """The secrets required to connect to Mailgun."""

    mailgun_api_key: str
    model_config = ConfigDict(extra="forbid")


class MessagingServiceSecretsTwilioSMS(BaseModel):
    """The secrets required to connect to Twilio SMS."""

    twilio_account_sid: str
    twilio_auth_token: str
    twilio_messaging_service_sid: Optional[str] = None
    twilio_sender_phone_number: Optional[PhoneNumber] = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        sender_phone = values.get("twilio_sender_phone_number")
        if not values.get("twilio_messaging_service_sid") and not sender_phone:
            raise ValueError(
                "Either the twilio_messaging_service_sid or the twilio_sender_phone_number should be supplied."
            )
        return values


class MessagingServiceSecretsTwilioEmail(BaseModel):
    """The secrets required to connect to twilio email."""

    twilio_api_key: str
    model_config = ConfigDict(extra="forbid")


class MessagingConfigBase(BaseModel):
    """Base model shared by messaging config related models"""

    service_type: MessagingServiceType
    details: Optional[
        Union[
            MessagingServiceDetailsMailgun,
            MessagingServiceDetailsTwilioEmail,
            MessagingServiceDetailsMailchimpTransactional,
        ]
    ] = None
    model_config = ConfigDict(
        use_enum_values=False, from_attributes=True, extra="forbid"
    )


class MessagingConfigRequestBase(MessagingConfigBase):
    """Base model shared by messaging config requests to provide validation on request inputs"""

    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        service_type = values.get("service_type")
        if service_type:
            # lowercase to match enums in database
            if isinstance(service_type, str):
                service_type = service_type.lower()

            # assign the transformed service_type value back into the values dict
            values["service_type"] = service_type
            cls.validate_details_schema(service_type, values.get("details", None))
        return values

    @staticmethod
    def validate_details_schema(
        service_type: Union[MessagingServiceType, str],
        details: Optional[Dict[str, Any]],
    ) -> None:
        if isinstance(service_type, MessagingServiceType):
            service_type = service_type.value
        if service_type == MessagingServiceType.mailgun.value:
            if not details:
                raise ValueError("Messaging config must include details")
            MessagingServiceDetailsMailgun.validate(details)
        if service_type == MessagingServiceType.twilio_email.value:
            if not details:
                raise ValueError("Messaging config must include details")
            MessagingServiceDetailsTwilioEmail.validate(details)


class MessagingConfigRequest(MessagingConfigRequestBase):
    """Messaging Config Request Schema"""

    name: str
    key: Optional[FidesKey] = None


class MessagingConfigResponse(MessagingConfigBase):
    """Messaging Config Response Schema"""

    name: str
    key: FidesKey
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


SUPPORTED_MESSAGING_SERVICE_SECRETS = Union[
    MessagingServiceSecretsMailgun,
    MessagingServiceSecretsTwilioSMS,
    MessagingServiceSecretsTwilioEmail,
    MessagingServiceSecretsMailchimpTransactional,
]


class MessagingConnectionTestStatus(Enum):
    """Enum for supplying statuses of validating credentials for a messaging Config"""

    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class TestMessagingStatusMessage(Msg):
    """A schema for testing functionality of a messaging config."""

    test_status: Optional[MessagingConnectionTestStatus] = None
    failure_reason: Optional[str] = None


class MessagingConfigStatus(Enum):
    """Enum for configuration statuses of a messaging config"""

    configured = "configured"
    not_configured = "not configured"


class MessagingConfigStatusMessage(BaseModel):
    """A schema for checking configuration status of message config."""

    config_status: Optional[MessagingConfigStatus] = None
    detail: Optional[str] = None


class BasicMessagingTemplateBase(BaseModel):
    type: str
    content: Dict[str, Any] = Field(
        examples=[
            {
                "subject": "Message subject",
                "body": "Custom message body",
            }
        ]
    )


class BasicMessagingTemplateRequest(BasicMessagingTemplateBase):
    pass


class BasicMessagingTemplateResponse(BasicMessagingTemplateBase):
    label: str


class BulkPutBasicMessagingTemplateResponse(BulkResponse):
    succeeded: List[BasicMessagingTemplateResponse]
    failed: List[BulkUpdateFailed]


class UserEmailInviteStatus(BaseModel):
    enabled: bool


class MessagingTemplateWithPropertiesBase(BaseModel):
    id: str
    type: str
    is_enabled: bool
    properties: Optional[List[MinimalProperty]] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class MessagingTemplateDefault(BaseModel):
    type: str
    is_enabled: bool
    content: Dict[str, Any] = Field(
        examples=[
            {
                "subject": "Message subject",
                "body": "Custom message body",
            }
        ]
    )


class MessagingTemplateWithPropertiesSummary(MessagingTemplateWithPropertiesBase):

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class MessagingTemplateWithPropertiesDetail(MessagingTemplateWithPropertiesBase):
    content: Dict[str, Any] = Field(
        examples=[
            {
                "subject": "Message subject",
                "body": "Custom message body",
            }
        ]
    )

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class MessagingTemplateWithPropertiesBodyParams(BaseModel):

    content: Dict[str, Any] = Field(
        examples=[
            {
                "subject": "Message subject",
                "body": "Custom message body",
            }
        ]
    )
    properties: Optional[List[str]] = None
    is_enabled: bool


class MessagingTemplateWithPropertiesPatchBodyParams(BaseModel):

    content: Optional[Dict[str, Any]] = Field(
        None,
        examples=[
            {
                "subject": "Message subject",
                "body": "Custom message body",
            }
        ],
    )
    properties: Optional[List[str]] = None
    is_enabled: Optional[bool] = None
