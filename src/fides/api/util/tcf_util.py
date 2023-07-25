from collections import defaultdict
from functools import lru_cache
from typing import Dict, List, Optional, Set

from fideslang.gvl import MAPPED_PURPOSES, MAPPED_SPECIAL_PURPOSES, data_use_to_purpose
from fideslang.gvl.models import MappedPurpose
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import array_agg
from sqlalchemy.orm import Query, Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_preference import PreferenceType
from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    PrivacyDeclaration,
    System,
)
from fides.api.schemas.tcf import (
    TCFExperienceContents,
    TCFPurposeRecord,
    TCFVendorRecord,
)

TCF_FIELD_LIST = [
    "tcf_purposes",
    "tcf_special_purposes",
    "tcf_vendors",
    "tcf_features",
    "tcf_special_features",
]


def get_preference_type_by_field_name(tcf_field_name: str):
    """Return PreferenceType Enum value given the TCF Field name"""
    return PreferenceType[tcf_field_name.replace("tcf_", "").rstrip("s")]


def get_purposes_and_vendors(
    db: Session, relevant_data_uses: List[str], purpose_field: str, purpose_map
):
    systems_uses_vendors: Query = (
        db.query(
            System.id,
            array_agg(PrivacyDeclaration.data_use).label("data_uses"),
            array_agg(func.distinct(ConnectionConfig.saas_config["type"])).label(
                "vendor"
            ),
        )
        .join(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
        .outerjoin(ConnectionConfig, ConnectionConfig.system_id == System.id)
        .group_by(System.id)
        .filter(PrivacyDeclaration.data_use.in_(relevant_data_uses))
    )

    relevant_purpose_ids: Dict[int, List[str]] = defaultdict(list)
    relevant_vendors: List[TCFVendorRecord] = []
    for record in systems_uses_vendors:
        vendor: Optional[str] = next(
            (vendor for vendor in record.vendor if vendor is not None), None
        )

        system_purpose_ids: Set[int] = set()
        for use in record.data_uses:
            system_purpose: Optional[MappedPurpose] = data_use_to_purpose(use)
            if system_purpose:
                system_purpose_ids.add(system_purpose.id)
                relevant_purpose_ids[system_purpose.id].extend(
                    [{"id": vendor, "name": vendor}] if vendor else []
                )

        if vendor:
            vendor_record = TCFVendorRecord(id=vendor)
            setattr(
                vendor_record,
                purpose_field,
                [purpose_map.get(purpose_id) for purpose_id in system_purpose_ids],
            )
            relevant_vendors.append(vendor_record)

    purpose_records = []
    for purpose_id, vendors in relevant_purpose_ids.items():
        purpose_record = TCFPurposeRecord(**purpose_map.get(purpose_id).dict())
        purpose_record.vendors = vendors
        purpose_records.append(purpose_record)

    return purpose_records, relevant_vendors


@lru_cache()
def get_tcf_contents(
    db: Session,
) -> TCFExperienceContents:
    """
    Load TCF Purposes from TCF_PATH and then return purposes whose data uses are parents/exact matches
    of data uses on systems, and vendors that contain these data uses.
    """
    all_tcf_data_uses: List[str] = []
    for purpose in MAPPED_PURPOSES.values():
        all_tcf_data_uses.extend(purpose.data_uses)

    purposes, vendors = get_purposes_and_vendors(
        db, all_tcf_data_uses, purpose_field="purposes", purpose_map=MAPPED_PURPOSES
    )

    special_purpose_data_uses: List[str] = []
    for special_purpose in MAPPED_SPECIAL_PURPOSES.values():
        special_purpose_data_uses.extend(special_purpose.data_uses)

    special_purposes, special_purpose_vendors = get_purposes_and_vendors(
        db,
        special_purpose_data_uses,
        purpose_field="special_purposes",
        purpose_map=MAPPED_SPECIAL_PURPOSES,
    )
    for special_purpose_vendor in special_purpose_vendors:
        matching_vendor = next(
            (vendor for vendor in vendors if vendor.id == special_purpose_vendor.id),
            None,
        )
        if matching_vendor:
            matching_vendor.special_purposes = special_purpose_vendor.special_purposes
        else:
            vendors.append(special_purpose_vendor)

    tcf_consent_contents = TCFExperienceContents()
    tcf_consent_contents.tcf_purposes = purposes
    tcf_consent_contents.tcf_special_purposes = special_purposes
    tcf_consent_contents.tcf_vendors = vendors
    return tcf_consent_contents
