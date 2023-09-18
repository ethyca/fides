from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple, Type, Union

from fideslang.gvl import (
    GVL_FEATURES,
    GVL_SPECIAL_FEATURES,
    MAPPED_PURPOSES,
    MAPPED_SPECIAL_PURPOSES,
    data_use_to_purpose,
    feature_id_to_feature_name,
    feature_name_to_feature,
    purpose_to_data_use,
)
from fideslang.gvl.models import Feature, Purpose
from fideslang.models import LegalBasisForProcessingEnum
from fideslang.validation import FidesKey
from sqlalchemy.engine.row import Row  # type:ignore[import]
from sqlalchemy.orm import Query, Session

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

TCFPurposeOrFeature = Union[TCFPurposeRecord, TCFFeatureRecord]

PURPOSE_DATA_USES: List[str] = []
for purpose in MAPPED_PURPOSES.values():
    PURPOSE_DATA_USES.extend(purpose.data_uses)

SPECIAL_PURPOSE_DATA_USES: List[str] = []
for special_purpose in MAPPED_SPECIAL_PURPOSES.values():
    SPECIAL_PURPOSE_DATA_USES.extend(special_purpose.data_uses)

ALL_GVL_DATA_USES = list(set(PURPOSE_DATA_USES) | set(SPECIAL_PURPOSE_DATA_USES))


class ConsentRecordType(Enum):
    """*ALL* of the relevant consent items that can be served or have preferences saved against.

    Includes notice items and tcf items
    """

    privacy_notice_id = "privacy_notice_id"
    privacy_notice_history_id = "privacy_notice_history_id"
    purpose = "purpose"
    special_purpose = "special_purpose"
    vendor = "vendor"
    system = "system"
    feature = "feature"
    special_feature = "special_feature"


# Each TCF section in the TCF Overlay mapped to the specific database column
# from which previously-saved values are retrieved
TCF_COMPONENT_MAPPING: Dict[str, ConsentRecordType] = {
    "tcf_purposes": ConsentRecordType.purpose,
    "tcf_special_purposes": ConsentRecordType.special_purpose,
    "tcf_features": ConsentRecordType.feature,
    "tcf_special_features": ConsentRecordType.special_feature,
    "tcf_vendors": ConsentRecordType.vendor,
    "tcf_systems": ConsentRecordType.system,  # Systems where there are no known vendor id -
    # we don't know the system "type"
}


class TCFComponentType(Enum):
    """A particular element of the TCF form"""

    purpose = "purpose"
    special_purpose = "special_purpose"
    vendor = "vendor"
    system = "system"
    feature = "feature"
    special_feature = "special_feature"


class TCFExperienceContents:
    """Class to serialize the initial contents of a TCF overlay

    Used to store GVL information pulled from Fideslang that has been combined with system data
    """

    tcf_purposes: List[TCFPurposeRecord] = []
    tcf_special_purposes: List[TCFPurposeRecord] = []
    tcf_vendors: List[TCFVendorRecord] = []
    tcf_features: List[TCFFeatureRecord] = []
    tcf_special_features: List[TCFFeatureRecord] = []
    tcf_systems: List[TCFVendorRecord] = []


def get_matching_privacy_declarations(db: Session) -> Query:
    """Returns flattened system/privacy declaration records where we have a matching gvl data use AND the
    legal basis for processing is "Consent" or "Legitimate interests"

    Only systems that meet this criteria should show up in the TCF overlay.
    """
    matching_privacy_declarations: Query = (
        db.query(
            System.id.label("system_id"),
            System.fides_key.label("system_fides_key"),
            System.name.label("system_name"),
            System.description.label("system_description"),
            System.vendor_id,
            PrivacyDeclaration.data_use,
            PrivacyDeclaration.legal_basis_for_processing,
            PrivacyDeclaration.features,
        )
        .join(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
        .filter(
            PrivacyDeclaration.data_use.in_(ALL_GVL_DATA_USES),
            PrivacyDeclaration.legal_basis_for_processing.in_(
                [
                    LegalBasisForProcessingEnum.CONSENT,
                    LegalBasisForProcessingEnum.LEGITIMATE_INTEREST,
                ]
            ),
        )
        .order_by(
            PrivacyDeclaration.created_at.desc()
        )  # Order to get repeatable results when collapsing information
    )
    return matching_privacy_declarations


def get_system_identifiers(
    privacy_declaration_row: Row,
) -> Tuple[Optional[str], str]:
    """Return the vendor id and overall system identifier (which is either the vendor OR system id)

    If a vendor exists, that's how we'll identify the system, and we'll consolidate information
    from multiple matching systems under that single vendor id.  If we don't have a vendor id, we don't know the
    "type" of system, so we'll surface information under that system id itself.
    """
    system_id: str = privacy_declaration_row["system_id"]
    vendor_id: Optional[str] = privacy_declaration_row["vendor_id"]
    system_identifier: str = vendor_id if vendor_id else system_id

    return vendor_id, system_identifier


def get_matching_data_uses_or_features(
    record: Row, relevant_uses_or_features: List[str], is_purpose_type: bool
) -> Set[str]:
    """
    Determine the set of relevant uses or features depending on whether we're building a
    purpose or feature section
    """
    if is_purpose_type:
        return (
            {record.data_use} if record.data_use in relevant_uses_or_features else set()
        )

    unique_features: Set[str] = set()
    for feature_name in record.features:
        if feature_name in relevant_uses_or_features:
            unique_features.add(feature_name)
    return unique_features


def _add_top_level_record_to_purpose_or_feature_section(
    matching_purpose_or_feature_map: Dict[int, TCFPurposeOrFeature],
    is_purpose_type: bool,
    use_or_feature: str,
) -> Optional[TCFPurposeOrFeature]:
    """
    Create a purpose or feature record, and add to the top-level [special] purposes or
    [special] features section if applicable.

    "matching_purpose_or_feature_map" is updated here, in-place.
    """

    tcf_section_type: Union[Type[TCFPurposeRecord], Type[TCFFeatureRecord]] = (
        TCFPurposeRecord if is_purpose_type else TCFFeatureRecord
    )
    get_gvl_record: Callable = (
        data_use_to_purpose if is_purpose_type else feature_name_to_feature
    )

    # Get the matching GVL record for the [special] purpose or [special] feature
    fideslang_gvl_record: Union[Purpose, Feature] = get_gvl_record(use_or_feature)
    if not fideslang_gvl_record:
        return None

    # Transform the base gvl record into the TCF record type that has more elements for TCF display.
    # Will be a top-level section.
    top_level_tcf_record: TCFPurposeOrFeature = tcf_section_type(
        **fideslang_gvl_record.dict()
    )

    # Add the TCF record to the top-level section in-place if it does not exist
    if top_level_tcf_record.id not in matching_purpose_or_feature_map:
        matching_purpose_or_feature_map[top_level_tcf_record.id] = top_level_tcf_record

    # Return the top-level record, whether we just created it, or it previously existed
    return matching_purpose_or_feature_map[top_level_tcf_record.id]


def _embed_purpose_or_feature_under_system(
    embedded_tcf_record: TCFPurposeOrFeature,
    system_section: Union[List[TCFPurposeRecord], List[TCFFeatureRecord]],
    legal_basis_for_processing: Optional[str],
) -> None:
    """
    Embed a second-level TCF purpose/feature under the systems section.

    The systems section is updated in-place.
    """
    existing_embedded_purpose_or_feature_record: Optional[TCFPurposeOrFeature] = next(
        (
            tcf_sub_record
            for tcf_sub_record in system_section
            if tcf_sub_record.id == embedded_tcf_record.id
        ),
        None,
    )

    if existing_embedded_purpose_or_feature_record:
        # Update legal_bases on existing embedded purpose or feature record beneath system if applicable
        _extend_legal_bases(
            existing_embedded_purpose_or_feature_record,
            legal_basis_for_processing,
            replace=False,
        )
        return

    # Nest new cloned TCF purpose or feature record beneath system otherwise
    # ensuring it has the appropriate legal basis
    _extend_legal_bases(embedded_tcf_record, legal_basis_for_processing, replace=True)
    system_section.append(embedded_tcf_record)  # type: ignore[arg-type]


def _embed_system_under_purpose_or_feature(
    top_level_tcf_record: TCFPurposeOrFeature,
    matching_purpose_or_feature_map: Dict[int, TCFPurposeOrFeature],
    privacy_declaration_row: Row,
) -> None:
    """
    Embed system/vendor information beneath the corresponding top-level TCF purpose/feature section.
    """

    vendor_id, system_identifier = get_system_identifiers(privacy_declaration_row)

    embedded_system_section: List[EmbeddedVendor] = (
        matching_purpose_or_feature_map[top_level_tcf_record.id].vendors
        if vendor_id
        else matching_purpose_or_feature_map[top_level_tcf_record.id].systems
    )

    if system_identifier not in [
        embedded_system_record.id for embedded_system_record in embedded_system_section
    ]:
        embedded_system_section.extend(
            [
                EmbeddedVendor(
                    id=system_identifier,
                    name=privacy_declaration_row.system_name,
                )
            ]
        )

    # Go ahead and sort embedded vendors by name while we're here.  Other sorting will occur at the end.
    embedded_system_section.sort(key=lambda x: x.name)


def build_purpose_or_feature_section_and_update_system_map(
    relevant_uses_or_features: List[str],
    tcf_component_name: str,
    system_map: Dict[str, TCFVendorRecord],
    matching_privacy_declaration_query: Query,
) -> Tuple[Dict[int, TCFPurposeOrFeature], Dict[str, TCFVendorRecord]]:
    """Builds a purpose or feature section of the TCF Overlay and makes corresponding updates to the systems section

    Represents information in multiple formats.  Puts purposes and features at the top-level and embeds vendor and systems
    information underneath.  Likewise, puts vendor and system information top-level, and embeds purpose and feature information
    underneath.

    System map is passed in as an argument instead of being constructed here, because both
    purposes/features are added to it and we modify that mapping multiple times.
    """
    matching_purpose_or_feature_map: Dict[int, TCFPurposeOrFeature] = {}

    is_purpose_section: bool = "purposes" in tcf_component_name

    for privacy_declaration_row in matching_privacy_declaration_query:
        # Filter relevant uses or features, depending on the section of the tcf overlay
        relevant_use_or_features: Set[str] = get_matching_data_uses_or_features(
            record=privacy_declaration_row,
            relevant_uses_or_features=relevant_uses_or_features,
            is_purpose_type=is_purpose_section,
        )
        legal_basis_for_processing: Optional[str] = privacy_declaration_row[
            "legal_basis_for_processing"
        ]

        for attribute in relevant_use_or_features:
            # Add top-level entry to purpose or feature section if applicable
            top_level_tcf_record: Optional[
                TCFPurposeOrFeature
            ] = _add_top_level_record_to_purpose_or_feature_section(
                matching_purpose_or_feature_map=matching_purpose_or_feature_map,
                is_purpose_type=is_purpose_section,
                use_or_feature=attribute,
            )

            if not top_level_tcf_record:
                continue

            vendor_id, system_identifier = get_system_identifiers(
                privacy_declaration_row
            )
            # Add top-level entry to the system section if applicable
            if system_identifier not in system_map:
                system_map[system_identifier] = TCFVendorRecord(
                    id=system_identifier,  # Identify system by vendor id if it exists, otherwise use system id.
                    name=privacy_declaration_row.system_name,
                    description=privacy_declaration_row.system_description,
                    has_vendor_id=bool(
                        vendor_id
                    ),  # Has_vendor_id will let us separate data into two sections: "tcf_vendors" and "tcf_systems"
                )

            # Embed the purpose/feature under the system if it doesn't exist, and/or consolidate legal bases
            _embed_purpose_or_feature_under_system(
                embedded_tcf_record=top_level_tcf_record.copy(),
                system_section=getattr(
                    system_map[system_identifier], tcf_component_name
                ),
                legal_basis_for_processing=legal_basis_for_processing,
            )

            # Append to the existing legal_bases on the top-level record if applicable for purpose
            # and special purpose sections. The top-level record is updated in-place
            _extend_legal_bases(
                top_level_tcf_record, legal_basis_for_processing, replace=False
            )

            # Finally, nest the system beneath this top level tcf record
            _embed_system_under_purpose_or_feature(
                top_level_tcf_record=top_level_tcf_record,
                matching_purpose_or_feature_map=matching_purpose_or_feature_map,
                privacy_declaration_row=privacy_declaration_row,
            )

    return matching_purpose_or_feature_map, system_map


def _extend_legal_bases(
    purpose_record: TCFPurposeOrFeature,
    legal_basis_for_processing: Optional[str],
    replace: bool = False,
) -> None:
    """Either appends or replaces the legal_bases, depending on whether replace=True or False

    purpose record updated in place
    """
    if not isinstance(purpose_record, TCFPurposeRecord):
        return

    legal_bases: List[str] = (
        [legal_basis_for_processing] if legal_basis_for_processing else []
    )

    if replace:
        purpose_record.legal_bases = legal_bases
    else:
        if legal_basis_for_processing not in purpose_record.legal_bases:
            purpose_record.legal_bases.extend(legal_bases)

    purpose_record.legal_bases.sort()


def get_tcf_contents(
    db: Session,
) -> TCFExperienceContents:
    """
    Returns the base contents of the TCF overlay.

    Queries for systems/privacy declarations that have a relevant GVL data use and a legal basis of Consent or Legitimate interests,
    and builds the TCF Overlay from these systems and privacy declarations.

    TCF Overlay has Purpose, Special Purpose, Feature, and Special Feature Sections, that have relevant systems and vendors embedded underneath.
    The reverse representation is also returned, and Vendors and Systems each have relevant Purpose, Special Purpose, Feature, and Special Feature sections.
    """
    system_map: Dict[str, TCFVendorRecord] = {}

    matching_privacy_declarations: Query = get_matching_privacy_declarations(db)

    # Collect purposes and update system map
    (
        purpose_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        PURPOSE_DATA_USES,
        tcf_component_name="purposes",
        system_map=system_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    # Collect special purposes and update system map
    (
        special_purpose_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        SPECIAL_PURPOSE_DATA_USES,
        tcf_component_name="special_purposes",
        system_map=updated_system_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    # Collect features and update system map
    (
        feature_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        [feature.name for feature in GVL_FEATURES.values()],
        tcf_component_name="features",
        system_map=updated_system_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    # Collect special features and update system map
    (
        special_feature_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        [feature.name for feature in GVL_SPECIAL_FEATURES.values()],
        tcf_component_name="special_features",
        system_map=updated_system_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    return combine_overlay_sections(
        purpose_map,  # type: ignore[arg-type]
        special_purpose_map,  # type: ignore[arg-type]
        feature_map,  # type: ignore[arg-type]
        special_feature_map,  # type: ignore[arg-type]
        updated_system_map,
    )


def combine_overlay_sections(
    purpose_map: Dict[int, TCFPurposeRecord],
    special_purpose_map: Dict[int, TCFPurposeRecord],
    feature_map: Dict[int, TCFFeatureRecord],
    special_feature_map: Dict[int, TCFFeatureRecord],
    updated_system_map: Dict[str, TCFVendorRecord],
) -> TCFExperienceContents:
    """Combine the different TCF sections and sort purposes/features by id, and vendors/systems by name"""
    tcf_consent_contents = TCFExperienceContents()
    tcf_consent_contents.tcf_purposes = _sort_by_id(purpose_map)  # type: ignore[assignment]
    tcf_consent_contents.tcf_special_purposes = _sort_by_id(special_purpose_map)  # type: ignore[assignment]
    tcf_consent_contents.tcf_features = _sort_by_id(feature_map)  # type: ignore[assignment]
    tcf_consent_contents.tcf_special_features = _sort_by_id(special_feature_map)  # type: ignore[assignment]

    sorted_vendors: List[TCFVendorRecord] = _sort_by_name(updated_system_map)  # type: ignore[assignment]
    for vendor in sorted_vendors:
        vendor.purposes.sort(key=lambda x: x.id)
        vendor.special_purposes.sort(key=lambda x: x.id)
        vendor.features.sort(key=lambda x: x.id)
        vendor.special_features.sort(key=lambda x: x.id)

    tcf_consent_contents.tcf_vendors = []
    tcf_consent_contents.tcf_systems = []

    # Separate system data into "tcf_vendors" and "tcf_systems" sections depending on whether we
    # know what "type" of vendor we have
    for system_or_vendor_record in sorted_vendors:
        if system_or_vendor_record.has_vendor_id:
            tcf_consent_contents.tcf_vendors.append(system_or_vendor_record)
        else:
            tcf_consent_contents.tcf_systems.append(system_or_vendor_record)

    return tcf_consent_contents


def _sort_by_id(
    tcf_mapping: Dict,
) -> Union[List[TCFPurposeRecord], List[TCFFeatureRecord], List[TCFVendorRecord]]:
    return sorted(list(tcf_mapping.values()), key=lambda x: x.id)


def _sort_by_name(
    tcf_mapping: Dict,
) -> Union[List[TCFPurposeRecord], List[TCFFeatureRecord], List[TCFVendorRecord]]:
    return sorted(list(tcf_mapping.values()), key=lambda x: x.name)


def systems_that_match_tcf_data_uses(
    matching_privacy_declarations: Query, data_uses: List[str]
) -> List[FidesKey]:
    """Check which systems have these data uses directly.

    This is used for determining relevant systems for TCF purposes and special purposes. Unlike
    determining relevant systems for Privacy Notices where we use a hierarchy-type matching,
    for TCF, we're looking for an exact match on data use."""
    if not data_uses:
        return []

    return list(
        {
            privacy_declaration_record.system_fides_key
            for privacy_declaration_record in matching_privacy_declarations.filter(
                PrivacyDeclaration.data_use.in_(data_uses)
            )
        }
    )


def get_relevant_systems_for_tcf_attribute(
    db: Session,
    tcf_field: Optional[str],
    tcf_value: Union[Optional[str], Optional[int]],
) -> List[FidesKey]:
    """Return a list of the system fides keys that match the given TCF attribute,
    provided the system is relevant for TCF.

    Used for consent reporting, to take a snapshot of the systems that are relevant at that point in time
    """

    # For TCF attributes, we need to first filter to systems/privacy declarations that have a relevant GVL data use
    # as well as a legal basis of processing of consent or legitimate interests
    starting_privacy_declarations: Query = get_matching_privacy_declarations(db)

    if tcf_field in [
        TCFComponentType.purpose.value,
        TCFComponentType.special_purpose.value,
    ]:
        purpose_data_uses: List[str] = purpose_to_data_use(tcf_value, special_purpose="special" in tcf_field)  # type: ignore[arg-type]
        return systems_that_match_tcf_data_uses(
            starting_privacy_declarations, purpose_data_uses
        )

    if tcf_field in [
        TCFComponentType.feature.value,
        TCFComponentType.special_feature.value,
    ]:
        return systems_that_match_tcf_feature(
            starting_privacy_declarations,
            feature_id_to_feature_name(
                feature_id=tcf_value, special_feature="special" in tcf_field  # type: ignore[arg-type]
            ),
        )

    if tcf_field == TCFComponentType.vendor.value:
        return systems_that_match_vendor_string(
            starting_privacy_declarations, tcf_value  # type: ignore[arg-type]
        )

    if tcf_field == TCFComponentType.system.value:
        return systems_that_match_system_id(starting_privacy_declarations, tcf_value)  # type: ignore[arg-type]

    return []


def systems_that_match_tcf_feature(
    matching_privacy_declarations: Query, feature: Optional[str]
) -> List[FidesKey]:
    """Check which systems have these data uses directly and are also relevant for TCF.

    This is used for determining relevant systems for TCF features and special features. Unlike
    determining relevant systems for Privacy Notices where we use a hierarchy-type matching,
    for TCF, we're looking for an exact match on feature."""
    if not feature:
        return []

    return list(
        {
            privacy_declaration_record.system_fides_key
            for privacy_declaration_record in matching_privacy_declarations.filter(
                PrivacyDeclaration.features.any(feature)
            )
        }
    )


def systems_that_match_vendor_string(
    matching_privacy_declarations: Query, vendor: Optional[str]
) -> List[FidesKey]:
    """Check which systems have this vendor associated with them and are relevant for TCF. Unlike PrivacyNotices,
    where we use hierarchy-type matching, with TCF components, we are looking for exact matches.
    """
    if not vendor:
        return []

    return list(
        {
            privacy_declaration_record.system_fides_key
            for privacy_declaration_record in matching_privacy_declarations.filter(
                System.vendor_id == vendor
            )
        }
    )


def systems_that_match_system_id(
    matching_privacy_declarations: Query, system_id: Optional[str]
) -> List[FidesKey]:
    """Returns the system id if it exists on the system and the system is relevant for TCF"""
    if not system_id:
        return []

    return list(
        {
            privacy_declaration_record.system_fides_key
            for privacy_declaration_record in matching_privacy_declarations.filter(
                System.id == system_id
            )
        }
    )
