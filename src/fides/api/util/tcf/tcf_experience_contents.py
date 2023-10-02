import json
from enum import Enum
from os.path import dirname, join
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
from loguru import logger
from sqlalchemy.engine.row import Row  # type:ignore[import]
from sqlalchemy.orm import Query, Session

from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    PrivacyDeclaration,
    System,
)
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.tcf import (
    EmbeddedVendor,
    TCFFeatureRecord,
    TCFPurposeConsentRecord,
    TCFPurposeLegitimateInterestsRecord,
    TCFSpecialFeatureRecord,
    TCFSpecialPurposeRecord,
    TCFVendorRecord,
    VendorConsentPreference,
    VendorLegitimateInterestsPreference,
)
from fides.config.helpers import load_file

_gvl: Optional[Dict] = None

GVL_PATH = join(
    dirname(__file__),
    "../../../data",
    "gvl.json",
)


NonVendorSectionType = Union[
    Type[TCFPurposeConsentRecord],
    Type[TCFPurposeLegitimateInterestsRecord],
    Type[TCFSpecialPurposeRecord],
    Type[TCFFeatureRecord],
    Type[TCFSpecialFeatureRecord],
]
NonVendorRecord = Union[
    TCFPurposeConsentRecord,
    TCFPurposeLegitimateInterestsRecord,
    TCFSpecialPurposeRecord,
    TCFFeatureRecord,
    TCFSpecialFeatureRecord,
]

SystemSubSections = Union[
    List[TCFPurposeConsentRecord],
    List[TCFPurposeLegitimateInterestsRecord],
    List[TCFSpecialPurposeRecord],
    List[TCFFeatureRecord],
    List[TCFSpecialFeatureRecord],
]


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
    purpose_consent = "purpose_consent"
    purpose_legitimate_interests = "purpose_legitimate_interests"
    special_purpose = "special_purpose"
    vendor_consent = "vendor_consent"
    vendor_legitimate_interests = "vendor_legitimate_interests"
    system_consent = "system_consent"
    system_legitimate_interests = "system_legitimate_interests"
    feature = "feature"
    special_feature = "special_feature"


# Each TCF section in the TCF Overlay mapped to the specific database column
# from which previously-saved values are retrieved
TCF_NON_VENDOR_SECTIONS: Dict[str, ConsentRecordType] = {
    "tcf_consent_purposes": ConsentRecordType.purpose_consent,
    "tcf_legitimate_interests_purposes": ConsentRecordType.purpose_legitimate_interests,
    "tcf_special_purposes": ConsentRecordType.special_purpose,
    "tcf_features": ConsentRecordType.feature,
    "tcf_special_features": ConsentRecordType.special_feature,
}


class VendorConsent:
    consent = ConsentRecordType.vendor_consent
    legitimate_interests = ConsentRecordType.vendor_legitimate_interests


class SystemConsent:
    consent = ConsentRecordType.system_consent
    legitimate_interests = ConsentRecordType.system_legitimate_interests


TCF_VENDOR_SECTIONS: Dict[str, Union[Type[VendorConsent], Type[SystemConsent]]] = {
    "tcf_vendors": VendorConsent,
    "tcf_systems": SystemConsent,  # Systems where there are no known vendor id -# we don't know the system "type"
}

TCF_SECTION_MAPPING = {**TCF_VENDOR_SECTIONS, **TCF_NON_VENDOR_SECTIONS}  # type: ignore[arg-type]


class TCFComponentType(Enum):
    """A particular element of the TCF form"""

    purpose_consent = "purpose_consent"
    purpose_legitimate_interests = "purpose_legitimate_interests"
    special_purpose = "special_purpose"
    vendor_consent = "vendor_consent"
    vendor_legitimate_interests = "vendor_legitimate_interests"
    system_consent = "system_consent"
    system_legitimate_interests = "system_legitimate_interests"
    feature = "feature"
    special_feature = "special_feature"


class TCFExperienceContents(FidesSchema):
    """Class to serialize the initial contents of a TCF overlay

    Used to store GVL information pulled from Fideslang that has been combined with system data
    """

    tcf_consent_purposes: List[TCFPurposeConsentRecord] = []
    tcf_legitimate_interests_purposes: List[TCFPurposeLegitimateInterestsRecord] = []
    tcf_special_purposes: List[TCFSpecialPurposeRecord] = []
    tcf_vendors: List[TCFVendorRecord] = []
    tcf_features: List[TCFFeatureRecord] = []
    tcf_special_features: List[TCFSpecialFeatureRecord] = []
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
    tcf_component_type: NonVendorSectionType,
    non_vendor_record_map: Dict[int, NonVendorRecord],
    is_purpose_type: bool,
    use_or_feature: str,
) -> Optional[NonVendorRecord]:
    """
    Create a purpose or feature record and add to the top-level sections.

    "non_vendor_record_map" is updated here, in-place.
    """

    get_gvl_record: Callable = (
        data_use_to_purpose if is_purpose_type else feature_name_to_feature
    )

    # Get the matching GVL record given the data use or feature found on the privacy declaration
    fideslang_gvl_record: Union[Purpose, Feature] = get_gvl_record(use_or_feature)
    if not fideslang_gvl_record:
        return None

    # Transform the base gvl record into the TCF record type that has more elements for TCF display.
    # Will be a top-level section.
    top_level_tcf_record: NonVendorRecord = tcf_component_type(
        **fideslang_gvl_record.dict()
    )

    # Add the TCF record to the top-level section in-place if it does not exist
    if top_level_tcf_record.id not in non_vendor_record_map:
        non_vendor_record_map[top_level_tcf_record.id] = top_level_tcf_record

    # Return the top-level record, whether we just created it, or it previously existed
    return non_vendor_record_map[top_level_tcf_record.id]


def _embed_purpose_or_feature_under_system(
    embedded_tcf_record: NonVendorRecord,
    system_section: SystemSubSections,
) -> None:
    """
    Embed a second-level TCF purpose/feature under the systems section.

    The systems section is updated in-place.
    """
    embedded_non_vendor_record: Optional[NonVendorRecord] = next(
        (
            tcf_sub_record
            for tcf_sub_record in system_section
            if tcf_sub_record.id == embedded_tcf_record.id
        ),
        None,
    )

    if embedded_non_vendor_record:
        return

    # Nest new cloned TCF purpose or feature record beneath system otherwise
    system_section.append(embedded_tcf_record)  # type: ignore[arg-type]


def _embed_system_under_purpose_or_feature(
    top_level_tcf_record: NonVendorRecord,
    non_vendor_record_map: Dict[int, NonVendorRecord],
    privacy_declaration_row: Row,
) -> None:
    """
    Embed system/vendor information beneath the corresponding top-level purpose or feature section.
    """

    vendor_id, system_identifier = get_system_identifiers(privacy_declaration_row)

    embedded_system_section: List[EmbeddedVendor] = (
        non_vendor_record_map[top_level_tcf_record.id].vendors
        if vendor_id
        else non_vendor_record_map[top_level_tcf_record.id].systems
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
    tcf_component_type: Union[
        Type[TCFPurposeConsentRecord],
        Type[TCFPurposeLegitimateInterestsRecord],
        Type[TCFSpecialPurposeRecord],
        Type[TCFFeatureRecord],
        Type[TCFSpecialFeatureRecord],
    ],
    vendor_section_name: str,
    system_map: Dict[str, TCFVendorRecord],
    matching_privacy_declaration_query: Query,
) -> Tuple[Dict[int, NonVendorRecord], Dict[str, TCFVendorRecord]]:
    """Builds a purpose or feature section of the TCF Overlay and makes corresponding updates to the systems section

    Represents information in multiple formats.  Puts purposes and features at the top-level and embeds vendor and systems
    information underneath.  Likewise, puts vendor and system information top-level, and embeds purpose and feature information
    underneath.

    System map is passed in as an argument instead of being constructed here, because both
    purposes/features are added to it and we modify that mapping multiple times.
    """
    non_vendor_record_map: Dict[int, NonVendorRecord] = {}

    is_purpose_section: bool = tcf_component_type in [
        TCFPurposeConsentRecord,
        TCFPurposeLegitimateInterestsRecord,
        TCFSpecialPurposeRecord,
    ]

    for privacy_declaration_row in matching_privacy_declaration_query:
        # Filter relevant uses or features, depending on the section of the tcf overlay
        relevant_use_or_features: Set[str] = get_matching_data_uses_or_features(
            record=privacy_declaration_row,
            relevant_uses_or_features=relevant_uses_or_features,
            is_purpose_type=is_purpose_section,
        )

        for attribute in relevant_use_or_features:
            # Add top-level entry to purpose or feature section if applicable
            top_level_tcf_record: Optional[
                NonVendorRecord
            ] = _add_top_level_record_to_purpose_or_feature_section(
                tcf_component_type=tcf_component_type,
                non_vendor_record_map=non_vendor_record_map,
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
                    ),  # Has_vendor_id will let us separate data into two sections: "tcf_vendors" and "tcf_systems",
                    consent_preference=VendorConsentPreference(id=system_identifier),
                    legitimate_interests_preference=VendorLegitimateInterestsPreference(
                        id=system_identifier
                    ),
                )

            # Embed the purpose/feature under the system if it doesn't exist, and/or consolidate legal bases
            _embed_purpose_or_feature_under_system(
                embedded_tcf_record=top_level_tcf_record.copy(),
                system_section=getattr(
                    system_map[system_identifier], vendor_section_name
                ),
            )

            # Finally, nest the system beneath this top level tcf record
            _embed_system_under_purpose_or_feature(
                top_level_tcf_record=top_level_tcf_record,
                non_vendor_record_map=non_vendor_record_map,
                privacy_declaration_row=privacy_declaration_row,
            )

    return non_vendor_record_map, system_map


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

    # Collect purposes with a legal basis of consent and update system map
    (
        purpose_consent_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        PURPOSE_DATA_USES,
        tcf_component_type=TCFPurposeConsentRecord,
        vendor_section_name="consent_purposes",
        system_map=system_map,
        matching_privacy_declaration_query=matching_privacy_declarations.filter(
            PrivacyDeclaration.legal_basis_for_processing
            == LegalBasisForProcessingEnum.CONSENT
        ),
    )

    # Collect purposes with a legal basis of legitimate interests and update system map
    (
        purpose_legitimate_interests_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        PURPOSE_DATA_USES,
        tcf_component_type=TCFPurposeLegitimateInterestsRecord,
        vendor_section_name="legitimate_interests_purposes",
        system_map=system_map,
        matching_privacy_declaration_query=matching_privacy_declarations.filter(
            PrivacyDeclaration.legal_basis_for_processing
            == LegalBasisForProcessingEnum.LEGITIMATE_INTEREST
        ),
    )

    # Collect special purposes and update system map
    (
        special_purpose_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        SPECIAL_PURPOSE_DATA_USES,
        tcf_component_type=TCFSpecialPurposeRecord,
        vendor_section_name="special_purposes",
        system_map=updated_system_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    # Collect features and update system map
    (
        feature_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        [feature.name for feature in GVL_FEATURES.values()],
        tcf_component_type=TCFFeatureRecord,
        vendor_section_name="features",
        system_map=updated_system_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    # Collect special features and update system map
    (
        special_feature_map,
        updated_system_map,
    ) = build_purpose_or_feature_section_and_update_system_map(
        [feature.name for feature in GVL_SPECIAL_FEATURES.values()],
        tcf_component_type=TCFSpecialFeatureRecord,
        vendor_section_name="special_features",
        system_map=updated_system_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    return combine_overlay_sections(
        purpose_consent_map,  # type: ignore[arg-type]
        purpose_legitimate_interests_map,  # type: ignore[arg-type]
        special_purpose_map,  # type: ignore[arg-type]
        feature_map,  # type: ignore[arg-type]
        special_feature_map,  # type: ignore[arg-type]
        updated_system_map,
    )


def combine_overlay_sections(
    purpose_consent_map: Dict[int, TCFPurposeConsentRecord],
    purpose_legitimate_interests_map: Dict[int, TCFPurposeLegitimateInterestsRecord],
    special_purpose_map: Dict[int, TCFSpecialPurposeRecord],
    feature_map: Dict[int, TCFFeatureRecord],
    special_feature_map: Dict[int, TCFFeatureRecord],
    updated_system_map: Dict[str, TCFVendorRecord],
) -> TCFExperienceContents:
    """Combine the different TCF sections and sort purposes/features by id, and vendors/systems by name"""
    tcf_consent_contents = TCFExperienceContents()
    tcf_consent_contents.tcf_consent_purposes = _sort_by_id(purpose_consent_map)  # type: ignore[assignment]
    tcf_consent_contents.tcf_legitimate_interests_purposes = _sort_by_id(purpose_legitimate_interests_map)  # type: ignore[assignment]
    tcf_consent_contents.tcf_special_purposes = _sort_by_id(special_purpose_map)  # type: ignore[assignment]
    tcf_consent_contents.tcf_features = _sort_by_id(feature_map)  # type: ignore[assignment]
    tcf_consent_contents.tcf_special_features = _sort_by_id(special_feature_map)  # type: ignore[assignment]

    sorted_vendors: List[TCFVendorRecord] = _sort_by_name(updated_system_map)  # type: ignore[assignment]
    for vendor in sorted_vendors:
        vendor.consent_purposes.sort(key=lambda x: x.id)
        vendor.legitimate_interests_purposes.sort(key=lambda x: x.id)
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
) -> SystemSubSections:
    return sorted(list(tcf_mapping.values()), key=lambda x: x.id)


def _sort_by_name(
    tcf_mapping: Dict,
) -> Union[
    List[TCFPurposeConsentRecord], List[TCFFeatureRecord], List[TCFVendorRecord]
]:
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
        TCFComponentType.purpose_consent.value,
        TCFComponentType.purpose_legitimate_interests.value,
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

    if tcf_field in [
        TCFComponentType.vendor_consent.value,
        TCFComponentType.vendor_legitimate_interests.value,
    ]:
        return systems_that_match_vendor_string(
            starting_privacy_declarations, tcf_value  # type: ignore[arg-type]
        )

    if tcf_field == [
        TCFComponentType.system_consent.value,
        TCFComponentType.system_legitimate_interests.value,
    ]:
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


def load_gvl() -> Dict:
    global _gvl  # pylint: disable=W0603
    if _gvl is None:
        with open(load_file([GVL_PATH]), "r", encoding="utf-8") as file:
            logger.info("Loading GVL from file")
            _gvl = json.load(file)
            return _gvl

    logger.info("Loading GVL from memory")
    return _gvl
