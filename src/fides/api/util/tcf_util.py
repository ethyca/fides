from functools import lru_cache
from typing import Dict, List, Tuple

from fideslang.gvl import (
    GVL_FEATURES,
    GVL_SPECIAL_FEATURES,
    MAPPED_PURPOSES,
    MAPPED_SPECIAL_PURPOSES,
    data_use_to_purpose,
    feature_name_to_feature,
)
from fideslang.gvl.models import Feature, Purpose
from sqlalchemy.dialects.postgresql import array_agg
from sqlalchemy.orm import Query, Session

from fides.api.models.privacy_preference import ConsentRecordType
from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    PrivacyDeclaration,
    System,
)
from fides.api.schemas.tcf import (
    EmbeddedVendor,
    TCFFeatureRecord,
    TCFPurposeRecord,
    TCFVendorRecord,
)

# Each TCF sections embedded in the TCF Overlay mapped to the
# specific field name from which previously-saved values are retrieved
TCF_COMPONENT_MAPPING: Dict[str, ConsentRecordType] = {
    "tcf_purposes": ConsentRecordType.purpose,
    "tcf_special_purposes": ConsentRecordType.special_purpose,
    "tcf_vendors": ConsentRecordType.vendor,
    "tcf_features": ConsentRecordType.feature,
    "tcf_special_features": ConsentRecordType.special_feature,
}


class TCFExperienceContents:
    """Schema to serialize the initial contents of a TCF overlay when we pull mapped purposes and special purposes
    from the GVL in Fideslang and combine them with system data."""

    tcf_purposes: List[TCFPurposeRecord] = []
    tcf_special_purposes: List[TCFPurposeRecord] = []
    tcf_vendors: List[TCFVendorRecord] = []
    tcf_features: List[TCFFeatureRecord] = []
    tcf_special_features: List[TCFFeatureRecord] = []


def get_purposes_and_vendors(
    db: Session,
    relevant_data_uses: List[str],
    purpose_field: str,
    system_map: Dict[str, TCFVendorRecord],
) -> Tuple[Dict[int, TCFPurposeRecord], Dict[str, TCFVendorRecord]]:
    """Helper method for building data for purposes/special purposes and vendors

    - Vendor data is summarized on each purpose and purpose data is summarized on each vendor.
    - System map is passed in as an argument instead of being constructed here, because both
    special purposes and purposes are added to it and we modify that mapping multiple times.

    """
    purpose_map: Dict[int, TCFPurposeRecord] = {}
    # Get rows of system ids, data uses, and vendors identifiers that match "relevant_data_uses"
    matching_systems: Query = (
        db.query(
            System.id,
            System.name,
            System.description,
            System.vendor_id,
            array_agg(PrivacyDeclaration.data_use).label("data_uses"),
        )
        .join(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
        .group_by(System.id)
        .filter(PrivacyDeclaration.data_use.in_(relevant_data_uses))
    )

    for record in matching_systems:
        # Get looked-up vendor if it exists
        vendor_id = record["vendor_id"]
        if vendor_id and vendor_id not in system_map:
            system_map[vendor_id] = TCFVendorRecord(
                id=vendor_id, name=record.name, description=record.description
            )

        for use in record.data_uses:
            # Get the matching purpose or special purpose
            system_purpose: Purpose = data_use_to_purpose(use)
            if not system_purpose:
                continue

            if system_purpose.id not in purpose_map:
                # Collect relevant purpose or special purposes
                purpose_map[system_purpose.id] = TCFPurposeRecord(
                    **system_purpose.dict()
                )

            if vendor_id:
                # Embed vendor on the given purpose or special purpose
                purpose_map[system_purpose.id].vendors.extend(
                    [EmbeddedVendor(id=vendor_id, name=record.name)]
                )
                # Do the reverse, and append the purpose or the special purpose to the vendor
                getattr(system_map[vendor_id], purpose_field).append(system_purpose)

    for purpose in purpose_map.values():
        purpose.vendors.sort(key=lambda x: x.id)
    return purpose_map, system_map


def get_features_and_vendors(
    db: Session,
    relevant_features: List[str],
    feature_field: str,
    system_map: Dict[str, TCFVendorRecord],
) -> Tuple[Dict[int, TCFFeatureRecord], Dict[str, TCFVendorRecord]]:
    matching_systems: Query = (
        db.query(
            System.id,
            System.name,
            System.description,
            System.vendor_id,
            array_agg(PrivacyDeclaration.features).label("features"),
        )
        .join(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
        .filter(PrivacyDeclaration.features.overlap(set(relevant_features)))
        .group_by(System.id)
    )

    feature_map: Dict[int, TCFFeatureRecord] = {}
    for record in matching_systems:
        vendor_id = record["vendor_id"]
        if vendor_id and vendor_id not in system_map:
            system_map[vendor_id] = TCFVendorRecord(
                id=vendor_id, name=record.name, description=record.description
            )

        unique_features = set()
        for feature_list in record.features:
            for feature_name in feature_list:
                unique_features.add(feature_name)

        for feature_name in unique_features:
            if feature_name not in relevant_features:
                continue
            feature: Feature = feature_name_to_feature(feature_name)
            if not feature:
                continue

            if feature.id not in feature_map:
                feature_map[feature.id] = TCFFeatureRecord(**feature.dict())

            if vendor_id:
                # Embed vendor on the given feature or special feature
                feature_map[feature.id].vendors.extend(
                    [EmbeddedVendor(id=vendor_id, name=record.name)]
                )
                # Do the reverse, and append the feature or the special feature to the vendor
                getattr(system_map[vendor_id], feature_field).append(feature)

    for feature_record in feature_map.values():
        feature_record.vendors.sort(key=lambda x: x.id)
    return feature_map, system_map


@lru_cache()
def get_tcf_contents(
    db: Session,
) -> TCFExperienceContents:
    """
    Load TCF Purposes and Special Purposes from Fideslang and then return a subset of those whose data uses
    are on systems. Return a reverse representation for the vendors themselves.

    TODO: TCF Populate TCF Experience with Features and Special Features
    TODO: TCF Return more Vendor information
    TODO: TCF Pull Vendor field from System instead of Integration
    """
    system_map: Dict[str, TCFVendorRecord] = {}

    # Collect purposes and systems
    all_tcf_data_uses: List[str] = []
    for purpose in MAPPED_PURPOSES.values():
        all_tcf_data_uses.extend(purpose.data_uses)
    purpose_map, updated_system_map = get_purposes_and_vendors(
        db, all_tcf_data_uses, purpose_field="purposes", system_map=system_map
    )

    # Collect special purposes and update system map
    special_purpose_data_uses: List[str] = []
    for special_purpose in MAPPED_SPECIAL_PURPOSES.values():
        special_purpose_data_uses.extend(special_purpose.data_uses)
    special_purpose_map, updated_system_map = get_purposes_and_vendors(
        db,
        special_purpose_data_uses,
        purpose_field="special_purposes",
        system_map=updated_system_map,
    )

    # Collect features and update system map
    feature_map, updated_system_map = get_features_and_vendors(
        db,
        [feature.name for feature in GVL_FEATURES.values()],
        feature_field="features",
        system_map=updated_system_map,
    )

    # Collect special features and update system map
    special_feature_map, updated_system_map = get_features_and_vendors(
        db,
        [feature.name for feature in GVL_SPECIAL_FEATURES.values()],
        feature_field="special_features",
        system_map=updated_system_map,
    )

    tcf_consent_contents = TCFExperienceContents()
    tcf_consent_contents.tcf_purposes = sorted(
        list(purpose_map.values()), key=lambda x: x.id
    )
    tcf_consent_contents.tcf_special_purposes = sorted(
        list(special_purpose_map.values()), key=lambda x: x.id
    )
    tcf_consent_contents.tcf_features = sorted(
        list(feature_map.values()), key=lambda x: x.id
    )
    tcf_consent_contents.tcf_special_features = sorted(
        list(special_feature_map.values()), key=lambda x: x.id
    )
    tcf_consent_contents.tcf_vendors = sorted(
        list(updated_system_map.values()), key=lambda x: x.id
    )
    for vendor in tcf_consent_contents.tcf_vendors:
        vendor.purposes.sort(key=lambda x: x.id)
        vendor.special_purposes.sort(key=lambda x: x.id)
        vendor.features.sort(key=lambda x: x.id)
        vendor.special_features.sort(key=lambda x: x.id)

    return tcf_consent_contents
