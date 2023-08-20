from functools import lru_cache
from typing import Dict, List, Tuple, Union, Type, Set, Callable

from sqlalchemy import func, case
from sqlalchemy.engine import Row

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


def get_system_features(record: Row, relevant_features: List[str]) -> Set[str]:
    """Collapses the relevant features across all the privacy declarations on the current system into a set.
    Sometimes the relevant features might be "TCF features" - other times they might be "TCF Special Features"
    """
    unique_features = set()
    for feature_list in record.features:
        for feature_name in feature_list:
            if feature_name in relevant_features:
                unique_features.add(feature_name)
    return unique_features


def get_tcf_component_and_vendors(
    db: Session,
    relevant_uses_or_features: List[str],
    tcf_component_name: str,
    system_map: Dict[str, TCFVendorRecord],
) -> Tuple[
    Dict[int, Union[TCFPurposeRecord, TCFFeatureRecord]], Dict[str, TCFVendorRecord]
]:
    """Helper method for building data for purposes/special purposes, features/special features and vendors

    - Vendor data is summarized on each purpose/feature and purpose/feature data is summarized on each vendor.
    - System map is passed in as an argument instead of being constructed here, because both
    purposes/features are added to it and we modify that mapping multiple times.
    """
    matching_record_map: Dict[int, Union[TCFPurposeRecord, TCFFeatureRecord]] = {}

    # Base query
    matching_systems: Query = (
        db.query(
            System.id,
            System.name,
            System.description,
            System.vendor_id,
            array_agg(PrivacyDeclaration.data_use).label("data_uses"),
            array_agg(
                case(
                    [
                        (
                            func.array_length(PrivacyDeclaration.features, 1) > 0,
                            PrivacyDeclaration.features,
                        )
                    ],
                    else_=[
                        "skip"
                    ],  # Default since you can't use array_agg on empty arrays.  ["skip"] is filtered out later.
                )
            ).label("features"),
        )
        .join(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
        .group_by(System.id)
    )

    tcf_record_type: Union[Type[TCFPurposeRecord], Type[TCFFeatureRecord]]
    tcf_method: Callable

    if tcf_component_name in ["purposes", "special_purposes"]:
        matching_systems = matching_systems.filter(
            PrivacyDeclaration.data_use.in_(relevant_uses_or_features)
        )
        tcf_record_type = TCFPurposeRecord
        tcf_method = data_use_to_purpose
    else:
        matching_systems = matching_systems.filter(
            PrivacyDeclaration.features.overlap(set(relevant_uses_or_features))
        )
        tcf_record_type = TCFFeatureRecord
        tcf_method = feature_name_to_feature

    for record in matching_systems:
        # Get looked-up vendor if it exists
        vendor_id = record["vendor_id"]
        if vendor_id and vendor_id not in system_map:
            system_map[vendor_id] = TCFVendorRecord(
                id=vendor_id, name=record.name, description=record.description
            )

        if tcf_component_name in ["purposes", "special_purposes"]:
            iterable_records = record.data_uses
        else:
            iterable_records: Set[str] = get_system_features(
                record, relevant_features=relevant_uses_or_features
            )

        for item in iterable_records:
            # Get the matching TCF Record
            fideslang_gvl_record: Union[Purpose, Feature] = tcf_method(item)
            if not fideslang_gvl_record:
                continue

            if fideslang_gvl_record.id not in matching_record_map:
                # Collect relevant TCF component
                matching_record_map[fideslang_gvl_record.id] = tcf_record_type(
                    **fideslang_gvl_record.dict()
                )

            if vendor_id:
                # Embed vendor on the given TCF component
                matching_record_map[fideslang_gvl_record.id].vendors.extend(
                    [EmbeddedVendor(id=vendor_id, name=record.name)]
                )
                # Do the reverse, and append the TCF component to the vendor
                getattr(system_map[vendor_id], tcf_component_name).append(
                    fideslang_gvl_record
                )

    return matching_record_map, system_map


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
    purpose_map, updated_system_map = get_tcf_component_and_vendors(
        db, all_tcf_data_uses, tcf_component_name="purposes", system_map=system_map
    )

    # Collect special purposes and update system map
    special_purpose_data_uses: List[str] = []
    for special_purpose in MAPPED_SPECIAL_PURPOSES.values():
        special_purpose_data_uses.extend(special_purpose.data_uses)
    special_purpose_map, updated_system_map = get_tcf_component_and_vendors(
        db,
        special_purpose_data_uses,
        tcf_component_name="special_purposes",
        system_map=updated_system_map,
    )

    # Collect features and update system map
    feature_map, updated_system_map = get_tcf_component_and_vendors(
        db,
        [feature.name for feature in GVL_FEATURES.values()],
        tcf_component_name="features",
        system_map=updated_system_map,
    )

    # Collect special features and update system map
    special_feature_map, updated_system_map = get_tcf_component_and_vendors(
        db,
        [feature.name for feature in GVL_SPECIAL_FEATURES.values()],
        tcf_component_name="special_features",
        system_map=updated_system_map,
    )

    tcf_consent_contents = TCFExperienceContents()
    tcf_consent_contents.tcf_purposes = _sort_by_id(purpose_map)
    tcf_consent_contents.tcf_special_purposes = _sort_by_id(special_purpose_map)
    tcf_consent_contents.tcf_features = _sort_by_id(feature_map)
    tcf_consent_contents.tcf_special_features = _sort_by_id(special_feature_map)
    tcf_consent_contents.tcf_vendors = _sort_by_id(updated_system_map)

    for vendor in tcf_consent_contents.tcf_vendors:
        vendor.purposes.sort(key=lambda x: x.id)
        vendor.special_purposes.sort(key=lambda x: x.id)
        vendor.features.sort(key=lambda x: x.id)
        vendor.special_features.sort(key=lambda x: x.id)
    tcf_consent_contents.tcf_vendors.sort(key=lambda x: x.id)

    return tcf_consent_contents


def _sort_by_id(
    tcf_mapping: Dict,
) -> List[Union[TCFPurposeRecord, TCFFeatureRecord, TCFVendorRecord]]:
    return sorted(list(tcf_mapping.values()), key=lambda x: x.id)
