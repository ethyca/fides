from functools import lru_cache
from typing import Callable, Dict, List, Optional, Set, Tuple, Type, Union

from fideslang.gvl import (
    GVL_FEATURES,
    GVL_SPECIAL_FEATURES,
    MAPPED_PURPOSES,
    MAPPED_SPECIAL_PURPOSES,
    data_use_to_purpose,
    feature_name_to_feature,
)
from fideslang.gvl.models import Feature, Purpose
from sqlalchemy import case, func
from sqlalchemy.dialects.postgresql import array_agg
from sqlalchemy.engine import Row
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
    "tcf_features": ConsentRecordType.feature,
    "tcf_special_features": ConsentRecordType.special_feature,
    "tcf_vendors": ConsentRecordType.vendor,
    "tcf_systems": ConsentRecordType.system_fides_key,  # Systems where there is no known vendor id
}


class TCFExperienceContents:
    """Schema to serialize the initial contents of a TCF overlay when we pull mapped purposes and special purposes
    from the GVL in Fideslang and combine them with system data."""

    tcf_purposes: List[TCFPurposeRecord] = []
    tcf_special_purposes: List[TCFPurposeRecord] = []
    tcf_vendors: List[TCFVendorRecord] = []
    tcf_features: List[TCFFeatureRecord] = []
    tcf_special_features: List[TCFFeatureRecord] = []
    tcf_systems: List[TCFVendorRecord] = []


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
    """Helper method for building data for a specific portion of the TCF overlay.

    Purposes and features have vendor/systems info enbedded, and vendor/system info has purposes and features embedded.

    - System map is passed in as an argument instead of being constructed here, because both
    purposes/features are added to it and we modify that mapping multiple times.
    """
    matching_record_map: Dict[int, Union[TCFPurposeRecord, TCFFeatureRecord]] = {}

    # Base query
    matching_systems: Query = (
        db.query(
            System.id,
            System.fides_key,
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
        .order_by(
            System.created_at.desc()
        )  # Order by to get repeatable results when collapsing information
    )

    tcf_record_type: Union[Type[TCFPurposeRecord], Type[TCFFeatureRecord]]
    get_tcf_construct: Callable

    if tcf_component_name in ["purposes", "special_purposes"]:
        matching_systems = matching_systems.filter(
            PrivacyDeclaration.data_use.in_(relevant_uses_or_features)
        )
        tcf_record_type = TCFPurposeRecord
        get_tcf_construct = data_use_to_purpose
    else:
        matching_systems = matching_systems.filter(
            PrivacyDeclaration.features.overlap(relevant_uses_or_features)
        )
        tcf_record_type = TCFFeatureRecord
        get_tcf_construct = feature_name_to_feature

    for record in matching_systems:
        # Identify system by vendor id if it exists, otherwise use system fides key.
        system_fides_key: str = record["fides_key"]
        vendor_id: Optional[str] = record["vendor_id"]
        system_identifier: str = vendor_id if vendor_id else system_fides_key

        if system_identifier not in system_map:
            system_map[system_identifier] = TCFVendorRecord(
                id=system_identifier,
                name=record.name,
                description=record.description,
                has_vendor_id=bool(vendor_id),
            )

        # Pull the attributes we care about from the system record depending on the TCF component.
        relevant_system_attributes: Set[str] = (
            record.data_uses
            if tcf_component_name in ["purposes", "special_purposes"]
            else get_system_features(
                record, relevant_features=relevant_uses_or_features
            )
        )

        for item in relevant_system_attributes:
            # Get the matching TCF Record
            fideslang_gvl_record: Union[Purpose, Feature] = get_tcf_construct(item)
            if not fideslang_gvl_record:
                continue

            if fideslang_gvl_record.id not in matching_record_map:
                # Collect relevant TCF component
                matching_record_map[fideslang_gvl_record.id] = tcf_record_type(
                    **fideslang_gvl_record.dict()
                )

            # Embed the systems information beneath the TCF component data
            embedded_system_or_vendor_record = (
                matching_record_map[fideslang_gvl_record.id].vendors
                if vendor_id
                else matching_record_map[fideslang_gvl_record.id].systems
            )

            if system_identifier not in [
                system_construct.id
                for system_construct in embedded_system_or_vendor_record
            ]:
                embedded_system_or_vendor_record.extend(
                    [EmbeddedVendor(id=system_identifier, name=record.name)]
                )

            # Do the reverse, and embed the TCF component under the systems subsection
            system_tcf_subsection = getattr(
                system_map[system_identifier], tcf_component_name
            )
            if fideslang_gvl_record.id not in [
                tcf_record.id for tcf_record in system_tcf_subsection
            ]:
                system_tcf_subsection.append(fideslang_gvl_record)

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

    sorted_vendors = _sort_by_id(updated_system_map)
    for vendor in sorted_vendors:
        vendor.purposes.sort(key=lambda x: x.id)
        vendor.special_purposes.sort(key=lambda x: x.id)
        vendor.features.sort(key=lambda x: x.id)
        vendor.special_features.sort(key=lambda x: x.id)

    tcf_consent_contents.tcf_vendors = list(
        filter(lambda vendor_record: vendor_record.has_vendor_id, sorted_vendors)
    )
    tcf_consent_contents.tcf_systems = list(
        filter(lambda vendor_record: not vendor_record.has_vendor_id, sorted_vendors)
    )

    return tcf_consent_contents


def _sort_by_id(
    tcf_mapping: Dict,
) -> List[Union[TCFPurposeRecord, TCFFeatureRecord, TCFVendorRecord]]:
    return sorted(list(tcf_mapping.values()), key=lambda x: x.id)
