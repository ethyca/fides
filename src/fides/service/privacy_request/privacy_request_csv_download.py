import csv
import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Query, Session
from starlette.responses import StreamingResponse

from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus


def privacy_request_csv_download(
    db: Session, privacy_request_query: Query
) -> StreamingResponse:
    """Download privacy requests as CSV for Admin UI"""
    f = io.StringIO()
    csv_file = csv.writer(f)

    # Execute query once and convert to list to avoid multiple iterations
    privacy_requests: List[PrivacyRequest] = privacy_request_query.all()
    privacy_request_ids: List[str] = [r.id for r in privacy_requests]

    denial_audit_log_query: Query = db.query(AuditLog).filter(
        AuditLog.action == AuditLogAction.denied,
        AuditLog.privacy_request_id.in_(privacy_request_ids),
    )
    denial_audit_logs: Dict[str, str] = {
        r.privacy_request_id: r.message for r in denial_audit_log_query
    }

    identity_columns, custom_field_columns = get_variable_columns(privacy_requests)

    csv_file.writerow(
        [
            "Status",
            "Request Type",
            "Time Received",
            "Deadline",
            "Reviewed By",
            "Request ID",
            "Time Approved/Denied",
            "Denial Reason",
            "Last Updated",
            "Completed On",
        ]
        + identity_columns
        + with_prefix("Custom Field", list(custom_field_columns.values()))
    )

    pr: PrivacyRequest
    for pr in privacy_requests:
        denial_reason = (
            denial_audit_logs[pr.id]
            if pr.status == PrivacyRequestStatus.denied and pr.id in denial_audit_logs
            else None
        )

        action_types: List[str] = []
        if pr and pr.policy:
            for rule in pr.policy.rules or []:  # type: ignore
                action_types.append(rule.action_type)

        deadline: Optional[datetime] = None
        if pr.days_left and pr.created_at:
            deadline = pr.created_at + timedelta(days=pr.days_left)

        static_cells = [
            pr.status.value if pr.status else None,
            ("+".join(action_types)),
            pr.created_at,
            deadline,
            pr.reviewed_by,
            pr.id,
            pr.reviewed_at,
            denial_reason,
            pr.updated_at,
            pr.finalized_at,
        ]

        identity_cells = extract_identity_cells(identity_columns, pr)
        custom_field_cells = extract_custom_field_cells(custom_field_columns, pr)

        row = static_cells + identity_cells + custom_field_cells

        csv_file.writerow(row)

    f.seek(0)
    response = StreamingResponse(f, media_type="text/csv")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=privacy_requests_download_{datetime.today().strftime('%Y-%m-%d')}.csv"
    )
    return response


def get_variable_columns(
    privacy_requests: List[PrivacyRequest],
) -> tuple[List[str], Dict[str, str]]:
    identity_columns: Set[str] = set()
    custom_field_columns: Dict[str, str] = {}

    for pr in privacy_requests:
        identity_columns.update(
            extract_identity_column_names(pr.get_persisted_identity().model_dump())
        )
        custom_field_columns.update(
            extract_custom_field_column_names(
                pr.get_persisted_custom_privacy_request_fields()
            )
        )

    return list(identity_columns), custom_field_columns


def extract_identity_column_names(identities: dict[str, Any]) -> Set[str]:
    """Extract column names from identity data that have non-empty values."""
    return {key for key, value in identities.items() if value}


def extract_custom_field_column_names(custom_fields: dict[str, Any]) -> Dict[str, str]:
    """Extract column names and labels from custom field data that have non-empty values."""
    return {
        key: value["label"]
        for key, value in custom_fields.items()
        if value.get("value")
    }


def with_prefix(prefix: str, items: List[str]) -> List[str]:
    return [f"{prefix} {item}" for item in items]


def extract_custom_field_cells(
    custom_field_columns: Dict[str, str], pr: PrivacyRequest
) -> List[str]:
    custom_fields = pr.get_persisted_custom_privacy_request_fields()
    return [
        custom_fields.get(custom_field_column, {}).get("value")
        for custom_field_column in custom_field_columns
    ]


def extract_identity_cells(
    identity_columns: List[str], pr: PrivacyRequest
) -> List[str]:
    identity = pr.get_persisted_identity()
    identity_dict = identity.model_dump()
    return [
        identity_dict.get(identity_column)  # type: ignore
        for identity_column in identity_columns
    ]
