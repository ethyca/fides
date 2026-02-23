import json
from datetime import datetime
from typing import Any, Callable, Dict, List

from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
    JWE_PAYLOAD_SYSTEMS,
)
from fides.api.oauth.jwt import generate_jwe
from fides.config import get_config

CONFIG = get_config()


def generate_auth_header_for_user(user, scopes):
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


def _generate_auth_header(oauth_client, app_encryption_key):
    client_id = oauth_client.id

    def _build_jwt(scopes):
        payload = {
            JWE_PAYLOAD_SCOPES: scopes,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), app_encryption_key)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


def generate_role_header_for_user(user, roles) -> Dict[str, str]:
    payload = {
        JWE_PAYLOAD_ROLES: roles,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }
    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    return {"Authorization": "Bearer " + jwe}


def _generate_auth_role_header(
    oauth_role_client, app_encryption_key
) -> Callable[[Any], Dict[str, str]]:
    client_id = oauth_role_client.id

    def _build_jwt(roles: List[str]) -> Dict[str, str]:
        payload = {
            JWE_PAYLOAD_ROLES: roles,
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        jwe = generate_jwe(json.dumps(payload), app_encryption_key)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt


def _generate_system_manager_header(
    oauth_system_client, app_encryption_key
) -> Callable[[Any], Dict[str, str]]:
    client_id = oauth_system_client.id

    def _build_jwt(systems: List[str]) -> Dict[str, str]:
        payload = {
            JWE_PAYLOAD_ROLES: [],
            JWE_PAYLOAD_CLIENT_ID: client_id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_SYSTEMS: systems,
        }
        jwe = generate_jwe(json.dumps(payload), app_encryption_key)
        return {"Authorization": "Bearer " + jwe}

    return _build_jwt
