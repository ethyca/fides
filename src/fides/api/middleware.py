import json
from typing import Any, Dict

from fastapi import Request
from loguru import logger
from sqlalchemy.orm import Session
from starlette.types import Message

from fides.api.api import deps
from fides.api.ctl.sql_models import AuditLogResource
from fides.api.oauth.utils import extract_client_id


async def handle_audit_log_resource(request: Request) -> None:
    """
    TODO: docs
    """
    audit_log_resource_data = {
        "user_id": None,
        "request_path": request.scope["path"],
        "request_type": request.method,
        "fides_keys": None,
        "extra_data": None,
    }
    db: Session = deps.get_api_session()
    token = request.headers.get("authorization")
    # possibly separate the token bits our for testability
    if token:
        client = await extract_client_id(token.replace("Bearer ", ""), db)
        audit_log_resource_data["user_id"] = client.user_id or "root"
    #
    fides_keys = await extract_data_from_body(request)
    audit_log_resource_data["fides_keys"] = fides_keys

    await write_audit_log_resource_record(db, audit_log_resource_data)


async def write_audit_log_resource_record(
    db: Session, audit_log_resource_data=Dict[str, Any]
) -> None:
    """
    Writes a record to the audit log resource table
    """
    try:
        AuditLogResource.create(db=db, data=audit_log_resource_data)
    except Exception as err:
        logger.info(err)


async def get_client_user_id(db: Session, auth_token: str) -> str:
    """
    Attempts to retrieve a client user_id
    """
    stripped_token = auth_token.replace("Bearer ", "")
    client = await extract_client_id(stripped_token, db)
    return client.user_id or "root"


async def extract_data_from_body(request: Request) -> Dict:
    """
    Attempts to retrieve a client user_id
    """
    await set_body(request, await request.body())

    body = await get_body(request)
    # b'{"description":"glop","fides_key":"glop","name":"glop","organization_fides_key":"default_organization","privacy_declarations":[],"system_dependencies":[],"system_type":"","tags":[],"third_country_transfers":[]}'

    # json.loads(body)
    # {'description': 'glop', 'fides_key': 'glop', 'name': 'glop', 'organization_fides_key': 'default_organization', 'privacy_declarations': [], 'system_dependencies': [], 'system_type': '', 'tags': [], 'third_country_transfers': []}
    # body_dict = json.loads(body)
    # if is a dict, check for fides_key. if list, iterate and check for fides key
    fides_keys = []
    if body:
        body = json.loads(body)
        if isinstance(body, dict):
            fides_key = body.get("fides_key")
            if fides_key:
                fides_keys.append(fides_key)
        if isinstance(body, list):
            for body_item in body:
                if isinstance(body_item, dict):
                    fides_key = body_item.get("fides_key")
                    if fides_key:
                        fides_keys.append(fides_key)
    return fides_keys


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body
