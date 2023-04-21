from typing import Any, Dict, List, Optional, Tuple, Type, Union

import yaml
from fastapi import HTTPException
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.ctl.sql_models import DataUse  # type: ignore[attr-defined]
from fides.api.ctl.sql_models import System  # type: ignore[attr-defined]
from fides.api.custom_types import SafeStr
from fides.api.ops.common_exceptions import ValidationError
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.privacy_notice import (
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeTemplate,
    check_conflicting_data_uses,
)
from fides.api.ops.models.privacy_preference import (
    PrivacyPreferenceHistory,
    UserConsentPreference,
)
from fides.api.ops.models.privacy_request import ExecutionLogStatus, PrivacyRequest
from fides.api.ops.schemas.privacy_notice import (
    PrivacyNoticeCreation,
    PrivacyNoticeWithId,
)


def filter_privacy_preferences_for_propagation(
    system: Optional[System], privacy_preferences: List[PrivacyPreferenceHistory]
) -> List[PrivacyPreferenceHistory]:
    """Filter privacy preferences on a privacy request to just the ones that should be considered for third party
    consent propagation"""

    propagatable_preferences: List[PrivacyPreferenceHistory] = [
        pref
        for pref in privacy_preferences
        if pref.privacy_notice_history.enforcement_level == EnforcementLevel.system_wide
        and pref.preference != UserConsentPreference.acknowledge
    ]

    if not system:
        return propagatable_preferences

    filtered_on_use: List[PrivacyPreferenceHistory] = []
    for pref in propagatable_preferences:
        if pref.privacy_notice_history.applies_to_system(system):
            filtered_on_use.append(pref)
    return filtered_on_use


def should_opt_in_to_service(
    system: Optional[System], privacy_request: PrivacyRequest
) -> Tuple[Optional[bool], List[PrivacyPreferenceHistory]]:
    """
    For SaaS Connectors, examine the Privacy Preferences and collapse this information into a single should we opt in? (True),
    should we opt out? (False) or should we do nothing? (None).

    Email connectors should instead call "filter_privacy_preferences_for_propagation" directly, since we can have preferences with
    conflicting opt in/opt out values for those connector types.

    Also return filtered preferences here so we can cache affected systems and/or secondary identifiers directly on these
    filtered preferences for consent reporting.

    - If using the old workflow (privacyrequest.consent_preferences), return True if all attached consent preferences
    are opt in, otherwise False.  System check is ignored.

    - If using the new workflow (privacyrequest.privacy_preferences), there is more filtering here.  Privacy Preferences
    must have an enforcement level of system-wide and a data use must match a system data use.  If the connector is
    orphaned (no system), skip the data use check. If conflicts, prefer the opt-out preference.
    """

    # OLD WORKFLOW
    if privacy_request.consent_preferences:
        return (
            all(
                consent_pref["opt_in"]
                for consent_pref in privacy_request.consent_preferences
            ),
            [],  # Don't need to return the filtered preferences, this is just relevant for the new workflow
        )

    # NEW WORKFLOW
    relevant_preferences = filter_privacy_preferences_for_propagation(
        system, privacy_request.privacy_preferences
    )
    if not relevant_preferences:
        return None, []  # We should do nothing here

    # Collapse relevant preferences into whether we should opt-in or opt-out
    preference_to_propagate: UserConsentPreference = (
        UserConsentPreference.opt_out
        if any(
            filtered_pref.preference == UserConsentPreference.opt_out
            for filtered_pref in relevant_preferences
        )
        else UserConsentPreference.opt_in
    )

    # Hopefully rare final filtering in case there are conflicting preferences
    filtered_preferences: List[PrivacyPreferenceHistory] = [
        pref
        for pref in relevant_preferences
        if pref.preference == preference_to_propagate
    ]

    # Return whether we should opt in, and the filtered preferences so we can update those for consent reporting
    return preference_to_propagate == UserConsentPreference.opt_in, filtered_preferences


def cache_initial_status_and_identities_for_consent_reporting(
    db: Session,
    privacy_request: PrivacyRequest,
    connection_config: ConnectionConfig,
    relevant_preferences: List[PrivacyPreferenceHistory],
    relevant_user_identities: Dict[str, Any],
) -> None:
    """Add a pending system status and cache relevant identities on the applicable PrivacyPreferenceHistory
    records for consent reporting.

    Preferences that aren't relevant for the given system/connector are given a skipped status.

    Typically used when *some* but not all privacy preferences are relevant.  Otherwise,
    other methods just mark all the preferences as skipped.
    """
    for pref in privacy_request.privacy_preferences:
        if pref in relevant_preferences:
            pref.update_secondary_user_ids(db, relevant_user_identities)
            pref.cache_system_status(
                db, connection_config.system_key, ExecutionLogStatus.pending
            )
        else:
            pref.cache_system_status(
                db, connection_config.system_key, ExecutionLogStatus.skipped
            )


def add_complete_system_status_for_consent_reporting(
    db: Session,
    privacy_request: PrivacyRequest,
    connection_config: ConnectionConfig,
) -> None:
    """Cache a complete system status for consent reporting on just the subset
    of preferences that were deemed relevant for the connector on failure

    Deeming them relevant if they already had a "pending" log added to them.
    """
    for pref in privacy_request.privacy_preferences:
        if (
            pref.affected_system_status
            and pref.affected_system_status.get(connection_config.system_key)
            == ExecutionLogStatus.pending.value
        ):
            pref.cache_system_status(
                db,
                connection_config.system_key,
                ExecutionLogStatus.complete,
            )


def add_errored_system_status_for_consent_reporting(
    db: Session,
    privacy_request: PrivacyRequest,
    connection_config: ConnectionConfig,
) -> None:
    """Cache an errored system status for consent reporting on just the subset
    of preferences that were deemed relevant for the connector on failure

    Deeming them relevant if they already had a "pending" log added to them.
    """
    for pref in privacy_request.privacy_preferences:
        if (
            pref.affected_system_status
            and pref.affected_system_status.get(connection_config.system_key)
            == ExecutionLogStatus.pending.value
        ):
            pref.cache_system_status(
                db,
                connection_config.system_key,
                ExecutionLogStatus.error,
            )


def validate_notice_data_uses(
    privacy_notices: List[Union[PrivacyNoticeWithId, PrivacyNoticeCreation]],
    db: Session,
) -> None:
    """
    Ensures that all the provided `PrivacyNotice`s have valid data uses.
    Raises a 422 HTTP exception if an unknown data use is found on any `PrivacyNotice`
    """
    valid_data_uses = [data_use.fides_key for data_use in DataUse.query(db).all()]
    try:
        for privacy_notice in privacy_notices:
            privacy_notice.validate_data_uses(valid_data_uses)
    except ValueError as e:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


def ensure_unique_ids(
    privacy_notices: List[PrivacyNoticeWithId],
) -> None:
    """
    Ensures that all the provided PrivacyNotices in the request body have unique ids
    Raises a 422 HTTP exception if there is more than one PrivacyNotice with the same ID
    """
    ids = set()
    for privacy_notice in privacy_notices:
        if privacy_notice.id not in ids:
            ids.add(privacy_notice.id)
        else:
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"More than one provided PrivacyNotice with ID {privacy_notice.id}.",
            )


def create_privacy_notices_util(
    db: Session, privacy_notice_schemas: List[PrivacyNoticeCreation]
) -> List[PrivacyNotice]:
    """Performs validation before creating Privacy Notices and Privacy Notice History records"""
    validate_notice_data_uses(privacy_notice_schemas, db)  # type: ignore[arg-type]

    existing_notices = PrivacyNotice.query(db).filter(PrivacyNotice.disabled.is_(False)).all()  # type: ignore[attr-defined]

    new_notices = [
        PrivacyNotice(**privacy_notice.dict(exclude_unset=True))
        for privacy_notice in privacy_notice_schemas
    ]
    check_conflicting_data_uses(new_notices, existing_notices)

    return [
        PrivacyNotice.create(
            db=db, data=privacy_notice.dict(exclude_unset=True), check_name=False
        )
        for privacy_notice in privacy_notice_schemas
    ]


def prepare_privacy_notice_patches(
    privacy_notice_updates: List[PrivacyNoticeWithId],
    db: Session,
    model: Union[Type[PrivacyNotice], Type[PrivacyNoticeTemplate]],
    allow_create: bool = False,
    ignore_disabled: bool = True,
) -> List[
    Tuple[PrivacyNoticeWithId, Optional[Union[PrivacyNotice, PrivacyNoticeTemplate]]]
]:
    """
    Prepares PrivacyNotice/Template creates and updates including performing data use
    conflict validation on proposed changes.

    Returns a list of tuples that have the PrivacyNotice update data (API schema) alongside
    their associated existing PrivacyNotice db record that will be updated

    :param privacy_notice_updates: List of privacy notice schemas with ids: appropriate
    for editing PrivacyNotices or upserting PrivacyNoticeTemplates
    :param db: Session
    :param model: one of PrivacyNotice or PrivacyNoticeTemplate
    :param allow_create: If True, this method can prepare data to be both created and updated. Otherwise,
    this is just intended for updates and will fail if a record doesn't exist.
    :param ignore_disabled: Should we skip checking disabled data uses?
    :return:
    """

    # first we populate a map of privacy notices/templates in the db, indexed by ID
    existing_notices: Dict[str, Union[PrivacyNotice, PrivacyNoticeTemplate]] = {}
    for existing_notice in model.query(db).all():
        existing_notices[existing_notice.id] = existing_notice

    # then associate existing notices/templates with their creates/updates
    # we'll return this set of data to actually process updates
    updates_and_existing: List[
        Tuple[
            PrivacyNoticeWithId, Optional[Union[PrivacyNotice, PrivacyNoticeTemplate]]
        ]
    ] = []
    for update_data in privacy_notice_updates:
        if update_data.id not in existing_notices:
            if not allow_create:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"No {model.__class__.__name__} found for id {update_data.id}.",
                )
            updates_and_existing.append((update_data, None))
        else:
            updates_and_existing.append((update_data, existing_notices[update_data.id]))

    # we temporarily store proposed update data in-memory for validation purposes only
    validation_updates = []
    for update_data, existing_notice in updates_and_existing:
        # add the patched update to our temporary updates for validation
        if existing_notice:
            validation_updates.append(
                existing_notice.dry_update(data=update_data.dict(exclude_unset=True))
            )
            # and don't include it anymore in the existing notices used for validation
            existing_notices.pop(existing_notice.id, None)
        else:
            # Add the pending created record to the the temporary updates for validation
            validation_updates.append(model(**update_data.dict(exclude_unset=True)))

    # run the validation here on our proposed "dry-run" updates
    try:
        check_conflicting_data_uses(
            validation_updates,
            existing_notices.values(),
            ignore_disabled=ignore_disabled,
        )
    except ValidationError as e:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)

    # return the tuples of update data associated with their existing db records
    return updates_and_existing


def upsert_privacy_notice_templates_util(
    db: Session,
    template_schemas: List[Union[PrivacyNoticeWithId]],
) -> List[PrivacyNoticeTemplate]:
    """
    Create or update existing privacy notice *templates*. These are the resources
    fides ships with out of the box.
    """
    ensure_unique_ids(template_schemas)
    validate_notice_data_uses(template_schemas, db)  # type: ignore[arg-type]

    creates_or_updates_and_existing: List[
        Tuple[PrivacyNoticeWithId, Optional[PrivacyNoticeTemplate]]
    ] = prepare_privacy_notice_patches(  # type: ignore[assignment]
        template_schemas,
        db,
        model=PrivacyNoticeTemplate,
        allow_create=True,
        ignore_disabled=False,
    )

    upserted_templates = []
    for (
        create_or_update_data,
        optional_existing_template,
    ) in creates_or_updates_and_existing:
        if optional_existing_template:
            upserted_templates.append(
                optional_existing_template.update(
                    db, data=create_or_update_data.dict(exclude_unset=True)
                )
            )
        else:
            upserted_templates.append(
                PrivacyNoticeTemplate.create(
                    db=db,
                    data=create_or_update_data.dict(exclude_unset=True),
                    check_name=False,
                )
            )
    return upserted_templates  # type: ignore[return-value]


def load_default_notices(
    db: Session, notice_yaml_file_path: str
) -> Tuple[List[PrivacyNoticeTemplate], List[PrivacyNotice]]:
    """
    Upserts any PrivacyNoticeTemplates from the provided file.
    If the id from the file exists in the PrivacyNoticeTemplates table, update
    the contents.  If the id doesn't exist, create a new template.

    Any new templates that don't have corresponding records in the PrivacyNotice and PrivacyNoticeHistory
    tables are added. Otherwise, we leave those records untouched.
    """
    logger.info(
        "Loading default privacy notice templates from {}", notice_yaml_file_path
    )
    with open(notice_yaml_file_path, "r", encoding="utf-8") as file:
        notices = yaml.safe_load(file).get("privacy_notices", [])

        template_schemas: List[PrivacyNoticeWithId] = []

        # Validate templates
        for privacy_notice_data in notices:
            template_schemas.append(PrivacyNoticeWithId(**privacy_notice_data))

        # Upsert Privacy Notice Templates
        privacy_notice_templates: List[
            PrivacyNoticeTemplate
        ] = upsert_privacy_notice_templates_util(db, template_schemas)

        # Determine which templates don't have corresponding records in PrivacyNotice
        new_templates: List[PrivacyNoticeTemplate] = [
            template
            for template in privacy_notice_templates
            if template.id
            not in [origin for (origin,) in db.query(PrivacyNotice.origin).all()]
        ]

        # Link Privacy Notice Schemas to the Privacy Notice Templates
        notice_schemas: List[PrivacyNoticeCreation] = []
        for template in new_templates:
            privacy_notice_schema = PrivacyNoticeCreation.from_orm(template)
            privacy_notice_schema.origin = SafeStr(template.id)
            notice_schemas.append(privacy_notice_schema)

        # Create PrivacyNotice and PrivacyNoticeHistory records only for new templates
        new_privacy_notices: List[PrivacyNotice] = create_privacy_notices_util(
            db, notice_schemas
        )

        return new_templates, new_privacy_notices
