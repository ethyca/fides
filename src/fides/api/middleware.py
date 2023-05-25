import json
from typing import Any, Dict, List

from fastapi import Request
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.types import Message

from fides.api.api import deps
from fides.api.ctl.sql_models import AuditLogResource  # type: ignore[attr-defined]
from fides.api.oauth.utils import extract_client_id


async def handle_audit_log_resource(request: Request) -> None:
    """
    Handles the lifecycle of recording audit log resource data.

    Attempts to track the WHO, WHEN, and beginning of WHAT for
    traceability purposes.

    WHO: User ID from the API request
    WHEN: Timestamps related to the request
    WHAT: The endpoint, request type, and (if applicable)
    fides_key(s) associated with the request
    """

    # details to be stored as a row on the server
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
    db: Session, audit_log_resource_data: Dict[str, Any]
) -> None:
    """
    Writes a record to the audit log resource table
    """
    try:
        AuditLogResource.create(db=db, data=audit_log_resource_data)
    except SQLAlchemyError as err:
        logger.debug(err)


async def get_client_user_id(db: Session, auth_token: str) -> str:
    """
    Attempts to retrieve a client user_id
    """
    stripped_token = auth_token.replace("Bearer ", "")
    client = await extract_client_id(stripped_token, db)
    return client.user_id or "root"


async def extract_data_from_body(request: Request) -> List:
    """
    Attempts to retrieve a client user_id
    """
    await set_body(request, await request.body())

    body = await get_body(request)

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


async def set_body(request: Request, body: bytes) -> None:
    """
    Sets the body return type for use in middleware
    """

    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive  # pylint: disable=W0212


async def get_body(request: Request) -> bytes:
    """awaits and sets the request body for use in middleware"""
    body = await request.body()
    await set_body(request, body)
    return body
