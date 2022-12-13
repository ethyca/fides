from typing import Any, Dict, List

import firebase_admin
from firebase_admin import App, auth, credentials
from firebase_admin.auth import UserRecord

from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.ops.util.collection_util import Row


@register("firebase_auth_user_access", [SaaSRequestType.READ])
def firebase_auth_user_access(  # pylint: disable=R0914
    node: TraversalNode,
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

    emails = input_data.get("email", [])
    for email in emails:
        user: UserRecord = auth.get_user_by_email(email, app=app)
        row = {"email": user.email, "uid": user.uid}
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
        processed_data.append(row)
    return processed_data


@register("firebase_auth_user_update", [SaaSRequestType.UPDATE])
def firebase_auth_user_update(
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
        email = row_param_values.get("email")
        user: UserRecord = auth.get_user_by_email(email, app=app)
        masked_fields = row_param_values["masked_object_fields"]
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
        email = row_param_values.get("email")
        user: UserRecord = auth.get_user_by_email(email, app=app)
        auth.delete_user(user.uid, app=app)
        rows_updated += 1
    return rows_updated


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
