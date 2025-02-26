import json
from typing import Any, Dict, List

from fastapi import Request
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.types import Message

from fides.api.api import deps
from fides.api.models.sql_models import AuditLogResource  # type: ignore[attr-defined]
from fides.api.oauth.utils import extract_token_and_load_client


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

    # get the user id associated with the request
    token = request.headers.get("authorization")
    if token:
        client = await get_client_user_id(db, token)
        audit_log_resource_data["user_id"] = client

    # Access request body to check for fides_keys
    await set_body(request, await request.body())

    body = await get_body(request)
    fides_keys: List = await extract_data_from_body(body)
    audit_log_resource_data["fides_keys"] = fides_keys

    # write record to server
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
    _, client = extract_token_and_load_client(stripped_token, db)
    return client.user_id or "root"


async def extract_data_from_body(body: bytes) -> List:
    """
    Attempts to retrieve any fides_keys associated with
    the request found in the request body.
    """

    fides_keys: List[str] = []
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

    Required due to shortcomings in Starlette with awaiting request
    body in middleware

    Reference: https://github.com/tiangolo/fastapi/issues/394#issuecomment-883524819
    """

    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive  # pylint: disable=W0212


async def get_body(request: Request) -> bytes:
    """
    Awaits and sets the request body for use in middleware


    Required due to shortcomings in Starlette with awaiting request
    body in middleware

    Reference: https://github.com/tiangolo/fastapi/issues/394#issuecomment-883524819
    """
    body = await request.body()
    await set_body(request, body)
    return body
