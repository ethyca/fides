from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from fideslang.default_taxonomy import DEFAULT_TAXONOMY
from fideslang.validation import FidesKey
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fides.api.custom_types import SafeStr
from fides.api.schemas import Msg
from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.messaging.shared_schemas import PossibleMessagingSecrets
from fides.api.schemas.privacy_preference import MinimalPrivacyPreferenceHistorySchema
from fides.api.schemas.privacy_request import Consent
from fides.api.schemas.property import MinimalProperty
from fides.api.schemas.redis_cache import IdentityBase


class MessagingMethod(Enum):
    """Enum for messaging method"""

    EMAIL = "email"
    SMS = "sms"


class MessagingServiceType(Enum):
    """Enum for messaging service type."""

    mailgun = "mailgun"
    twilio_text = "twilio_text"
    twilio_email = "twilio_email"
    mailchimp_transactional = "mailchimp_transactional"
    aws_ses = "aws_ses"

    @classmethod
    def _missing_(
        cls: Type[MessagingServiceType], value: Any
    ) -> Optional[MessagingServiceType]:
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return None

    @property
    def human_readable(self) -> str:
        """
        Human-readable mapping for MessagingServiceType
        """
        readable_mapping: Dict[str, str] = {
            MessagingServiceType.mailgun.value: "Mailgun",
            MessagingServiceType.twilio_text.value: "Twilio SMS",
            MessagingServiceType.twilio_email.value: "Twilio Email",
            MessagingServiceType.mailchimp_transactional.value: "Mailchimp Transactional",
            MessagingServiceType.aws_ses.value: "AWS SES",
        }
        try:
            return readable_mapping[self.value]
        except KeyError:
            raise NotImplementedError(
                "Add new MessagingServiceType to human_readable mapping"
            )


EMAIL_MESSAGING_SERVICES: Tuple[str, ...] = (
    MessagingServiceType.mailgun.value,
    MessagingServiceType.twilio_email.value,
    MessagingServiceType.mailchimp_transactional.value,
    MessagingServiceType.aws_ses.value,
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
    EXTERNAL_USER_WELCOME = "external_user_welcome"
    MANUAL_TASK_DIGEST = "manual_task_digest"
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
    MessagingActionType.MANUAL_TASK_DIGEST.value,
)


class MessagingTestBodyParams(BaseModel):
    """Body params required for testing messaging service"""

    to_identity: IdentityBase


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

    model_config = ConfigDict(extra="forbid")


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


class ExternalUserWelcomeBodyParams(BaseModel):
    """Body params required to send a welcome email to external users"""

    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    privacy_center_url: str
    access_token: str
    org_name: str


class ManualTaskDigestBodyParams(BaseModel):
    """Body params required to send manual task digest emails"""

    vendor_contact_name: str
    organization_name: str
    portal_url: str
    imminent_task_count: int
    upcoming_task_count: int
    total_task_count: int
    company_logo_url: Optional[str] = None


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
            ExternalUserWelcomeBodyParams,
        ]
    ] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_body_params_match_action_type(self) -> "FidesopsMessage":

        valid_body_params_for_action_type = {
            MessagingActionType.CONSENT_REQUEST: None,  # Don't validate this one
            MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT: ConsentEmailFulfillmentBodyParams,
            MessagingActionType.SUBJECT_IDENTITY_VERIFICATION: SubjectIdentityVerificationBodyParams,
            MessagingActionType.PRIVACY_REQUEST_RECEIPT: RequestReceiptBodyParams,
            MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY: RequestReviewDenyBodyParams,
            MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE: None,  # No body params for this action type
            MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS: AccessRequestCompleteBodyParams,
            MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT: ErasureRequestBodyParams,
            MessagingActionType.PRIVACY_REQUEST_ERROR_NOTIFICATION: ErrorNotificationBodyParams,
            MessagingActionType.USER_INVITE: UserInviteBodyParams,
            MessagingActionType.EXTERNAL_USER_WELCOME: ExternalUserWelcomeBodyParams,
            MessagingActionType.MANUAL_TASK_DIGEST: ManualTaskDigestBodyParams,
        }

        valid_body_params = valid_body_params_for_action_type.get(
            self.action_type, None
        )
        if valid_body_params and not isinstance(self.body_params, valid_body_params):
            raise ValueError(
                f"Invalid body params for action type {self.action_type}. Expected {valid_body_params.__name__}, got {type(self.body_params).__name__}"
            )

        return self


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

    # AWS SES
    AWS_REGION = "aws_region"


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


class MessagingServiceDetailsAWS_SES(BaseModel):
    """The details required to represent an AWS SES email configuration."""

    email_from: Optional[str] = None
    domain: Optional[str] = None
    aws_region: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not values.get("domain") and not values.get("email_from"):
            raise ValueError("Either 'email_from' or 'domain' must be provided.")
        return values


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

    # AWS SES
    AWS_AUTH_METHOD = "auth_method"
    AWS_ACCESS_KEY_ID = "aws_access_key_id"
    AWS_SECRET_ACCESS_KEY = "aws_secret_access_key"
    AWS_ASSUME_ROLE_ARN = "aws_assume_role_arn"


class MessagingConfigBase(BaseModel):
    """Base model shared by messaging config related models"""

    service_type: MessagingServiceType
    details: Optional[
        Union[
            MessagingServiceDetailsMailgun,
            MessagingServiceDetailsTwilioEmail,
            MessagingServiceDetailsMailchimpTransactional,
            MessagingServiceDetailsAWS_SES,
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

        if (
            service_type
            in [
                MessagingServiceType.mailgun.value,
                MessagingServiceType.twilio_email.value,
                MessagingServiceType.aws_ses.value,
            ]
            and not details
        ):
            raise ValueError("Messaging config must include details")

        if service_type == MessagingServiceType.mailgun.value:
            MessagingServiceDetailsMailgun.model_validate(details)
        if service_type == MessagingServiceType.twilio_email.value:
            MessagingServiceDetailsTwilioEmail.model_validate(details)
        if service_type == MessagingServiceType.aws_ses.value:
            MessagingServiceDetailsAWS_SES.model_validate(details)


class MessagingConfigRequest(MessagingConfigRequestBase):
    """Messaging Config Request Schema"""

    name: Optional[str] = None
    key: Optional[FidesKey] = None
    secrets: Optional[PossibleMessagingSecrets] = None


class MessagingConfigResponse(MessagingConfigBase):
    """Messaging Config Response Schema"""

    name: str
    key: FidesKey
    last_test_timestamp: Optional[datetime] = None
    last_test_succeeded: Optional[bool] = None


class MessagingConnectionTestStatus(Enum):
    """Enum for supplying statuses of validating credentials for a messaging Config"""

    succeeded = "succeeded"
    failed = "failed"


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
