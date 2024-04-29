from typing import Any, Dict, List

import firebase_admin
from firebase_admin import App, auth, credentials
from firebase_admin.auth import UserNotFoundError, UserRecord
from loguru import logger

from fides.api.common_exceptions import FidesopsException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row
from fides.api.util.logger import Pii
from fides.api.util.saas_util import get_identity


@register("firebase_auth_user_access", [SaaSRequestType.READ])
def firebase_auth_user_access(  # pylint: disable=R0914
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    SaaS Request Override function used to integrate access requests with
    Firebase Auth service. Specifically, it reads `User` records.
    """
    app = initialize_firebase(secrets)

    processed_data = []
    identity = get_identity(privacy_request)
    user: UserRecord
    if identity == "email":
        emails = input_data.get("email", [])
        for email in emails:
            try:
                user = auth.get_user_by_email(email, app=app)
                processed_data.append(user_record_to_row(user))
            except UserNotFoundError:
                logger.warning(
                    f"Could not find user with email {Pii(email)} in firebase"
                )
    elif identity == "phone_number":
        phone_numbers = input_data.get("phone_number", [])
        for phone_number in phone_numbers:
            try:
                user = auth.get_user_by_phone_number(phone_number, app=app)
                processed_data.append(user_record_to_row(user))
            except UserNotFoundError:
                logger.warning(
                    f"Could not find user with phone_number {Pii(phone_number)} in firebase"
                )
    else:
        raise FidesopsException(
            "Unsupported identity type for Firebase connector. Currently only `email` and `phone_number` are supported"
        )
    return processed_data


def user_record_to_row(user: UserRecord) -> Row:
    """
    Translates a Firebase `UserRecord` to a Fides access request result `Row`
    """
    row = {"uid": user.uid}
    keys = [
        "email",
        "uid",
        "display_name",
        "phone_number",
        "photo_url",
        "disabled",
        "email_verified",
    ]
    for key in keys:
        value = getattr(user, key)
        if value is not None:
            row[key] = value

    if user.provider_data:
        pds = []
        for pd in user.provider_data:
            pd_keys = ["display_name", "provider_id", "email", "photo_url"]
            pd_to_add = {}
            for key in pd_keys:
                value = getattr(pd, key)
                if value is not None:
                    pd_to_add[key] = value
            pds.append(pd_to_add)
        row["provider_data"] = pds
    return row


@register("firebase_auth_user_update", [SaaSRequestType.UPDATE])
def firebase_auth_user_update(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    SaaS Request Override function used to integrate update requests with
    Firebase Auth service. Specifically, it updates `User` records.
    """
    app = initialize_firebase(secrets)
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        user: UserRecord = retrieve_user_record(privacy_request, row_param_values, app)
        masked_fields = row_param_values["masked_object_fields"]
        email = masked_fields.get("email", user.email)
        display_name = masked_fields.get("display_name", user.display_name)
        phone_number = masked_fields.get("phone_number", user.phone_number)
        photo_url = masked_fields.get("photo_url", user.photo_url)
        disabled = masked_fields.get("disabled", user.disabled)
        email_verified = masked_fields.get("email_verified", user.email_verified)
        auth.update_user(
            user.uid,
            email=email,
            display_name=display_name,
            phone_number=phone_number,
            photo_url=photo_url,
            disabled=disabled,
            email_verified=email_verified,
            app=app,
        )
        rows_updated += 1
    return rows_updated


@register("firebase_auth_user_delete", [SaaSRequestType.DELETE])
def firebase_auth_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    SaaS Request Override function used to integrate delete requests with
    Firebase Auth service. Specifically, it deletes `User` records.

    Currently, this function is not invoked by any default configuration -
    instead, Firebase erasures are done via updates, and the update function
    defined above. We've kept this function implementation here so that
    it can be easily leveraged without code changes and by a simple config update.
    """
    app = initialize_firebase(secrets)
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        user: UserRecord = retrieve_user_record(privacy_request, row_param_values, app)
        auth.delete_user(user.uid, app=app)
        rows_updated += 1
    return rows_updated


def retrieve_user_record(
    privacy_request: PrivacyRequest, row_param_values: Dict[str, Any], app: App
) -> UserRecord:
    """
    Utility that erasure functions can use to retrieve a Firebase `UserRecord`
    """
    identity = get_identity(privacy_request)
    if identity == "email":
        email = row_param_values.get("email", [])
        return auth.get_user_by_email(email, app=app)
    if identity == "phone_number":
        phone_number = row_param_values.get("phone_number", [])
        return auth.get_user_by_phone_number(phone_number, app=app)

    raise FidesopsException(
        "Unsupported identity type for Firebase connector. Currently only `email` and `phone_number` are supported"
    )


def initialize_firebase(secrets: Dict[str, Any]) -> App:
    """
    Initializes a Firebase "app" instance based on the given
    secrets `dict`. The value of the `project_id` key of the
    secrets dict is used for the `name` of the Firebase app.
    """
    creds = get_firebase_credentials(secrets)
    project_id = creds.project_id
    try:
        app = firebase_admin.get_app(project_id)
    except ValueError:
        app = firebase_admin.initialize_app(credential=creds, name=project_id)
    return app


def get_firebase_credentials(secrets: Dict[str, Any]) -> credentials.Certificate:
    """
    Utility function to create a Firebase `credentials.Certificate` instance
    based on the provided secrets `dict`.
    """
    credential_keys = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
        "auth_provider_x509_cert_url",
        "client_x509_cert_url",
    ]
    creds = {key: secrets[key] for key in credential_keys}
    return credentials.Certificate(cert=creds)
