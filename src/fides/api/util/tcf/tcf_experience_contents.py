# mypy: disable-error-code="arg-type, attr-defined, assignment"
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
from sqlalchemy import and_, not_, or_
from sqlalchemy.engine.row import Row  # type:ignore[import]
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    PrivacyDeclaration,
    System,
)
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.tcf import (
    EmbeddedPurpose,
    EmbeddedVendor,
    TCFFeatureRecord,
    TCFPurposeConsentRecord,
    TCFPurposeLegitimateInterestsRecord,
    TCFSpecialFeatureRecord,
    TCFSpecialPurposeRecord,
    TCFVendorConsentRecord,
    TCFVendorLegitimateInterestsRecord,
    TCFVendorRelationships,
)
from fides.config import CONFIG
from fides.config.helpers import load_file

_gvl: Optional[Dict] = None

GVL_PATH = join(
    dirname(__file__),
    "../../../data",
    "gvl.json",
)

AC_PREFIX = "gacp."
GVL_PREFIX = "gvl."

PURPOSE_DATA_USES: List[str] = []
for purpose in MAPPED_PURPOSES.values():
    PURPOSE_DATA_USES.extend(purpose.data_uses)

SPECIAL_PURPOSE_DATA_USES: List[str] = []
for special_purpose in MAPPED_SPECIAL_PURPOSES.values():
    SPECIAL_PURPOSE_DATA_USES.extend(special_purpose.data_uses)

ALL_GVL_DATA_USES = list(set(PURPOSE_DATA_USES) | set(SPECIAL_PURPOSE_DATA_USES))

# Defining some types for the different TCF sections
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

VendorSectionType = Union[
    Type[TCFVendorConsentRecord],
    Type[TCFVendorLegitimateInterestsRecord],
    Type[TCFVendorRelationships],
]

VendorRecord = Union[
    TCFVendorConsentRecord, TCFVendorLegitimateInterestsRecord, TCFVendorRelationships
]

SystemSubSections = Union[
    List[TCFPurposeConsentRecord],
    List[TCFPurposeLegitimateInterestsRecord],
    List[TCFSpecialPurposeRecord],
    List[TCFFeatureRecord],
    List[TCFSpecialFeatureRecord],
]

# Common SQLAlchemy filters used below

# Define a special-case filter for AC Systems with no Privacy Declarations
AC_SYSTEM_NO_PRIVACY_DECL_FILTER: BooleanClauseList = and_(
    System.vendor_id.startswith(AC_PREFIX), PrivacyDeclaration.id.is_(None)
)

# Filter for any non-AC Systems
NOT_AC_SYSTEM_FILTER: BooleanClauseList = or_(
    not_(System.vendor_id.startswith(AC_PREFIX)), System.vendor_id.is_(None)
)
CONSENT_LEGAL_BASIS_FILTER: BinaryExpression = (
    PrivacyDeclaration.legal_basis_for_processing == LegalBasisForProcessingEnum.CONSENT
)
LEGITIMATE_INTEREST_LEGAL_BASIS_FILTER: BinaryExpression = (
    PrivacyDeclaration.legal_basis_for_processing
    == LegalBasisForProcessingEnum.LEGITIMATE_INTEREST
)

GVL_DATA_USE_FILTER: BinaryExpression = PrivacyDeclaration.data_use.in_(
    ALL_GVL_DATA_USES
)


class ConsentRecordType(Enum):
    """*ALL* of the relevant consent items that can be served or have preferences saved against.

    Includes two privacy notices fields, and then everything in TCFComponentType
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
TCF_SECTION_MAPPING: Dict[str, Optional[ConsentRecordType]] = {
    "tcf_purpose_consents": ConsentRecordType.purpose_consent,
    "tcf_purpose_legitimate_interests": ConsentRecordType.purpose_legitimate_interests,
    "tcf_special_purposes": ConsentRecordType.special_purpose,
    "tcf_features": ConsentRecordType.feature,
    "tcf_special_features": ConsentRecordType.special_feature,
    "tcf_vendor_consents": ConsentRecordType.vendor_consent,
    "tcf_vendor_legitimate_interests": ConsentRecordType.vendor_legitimate_interests,
    "tcf_vendor_relationships": None,
    "tcf_system_consents": ConsentRecordType.system_consent,
    "tcf_system_legitimate_interests": ConsentRecordType.system_legitimate_interests,
    "tcf_system_relationships": None,
}


class TCFComponentType(Enum):
    """A particular element of the TCF form against which preferences can be saved

    Note that system_relationships and vendor_relationships are not in this list
    """

    purpose_consent = "purpose_consent"
    purpose_legitimate_interests = "purpose_legitimate_interests"

    special_purpose = "special_purpose"
    feature = "feature"
    special_feature = "special_feature"

    vendor_consent = "vendor_consent"
    vendor_legitimate_interests = "vendor_legitimate_interests"

    system_consent = "system_consent"
    system_legitimate_interests = "system_legitimate_interests"


class TCFExperienceContents(
    FidesSchema
):  # pylint: disable=too-many-instance-attributes
    """Class to serialize the initial contents of a TCF overlay

    Used to store GVL information pulled from Fideslang that has been combined with system data
    """

    tcf_purpose_consents: List[TCFPurposeConsentRecord] = []
    tcf_purpose_legitimate_interests: List[TCFPurposeLegitimateInterestsRecord] = []

    tcf_special_purposes: List[TCFSpecialPurposeRecord] = []
    tcf_features: List[TCFFeatureRecord] = []
    tcf_special_features: List[TCFSpecialFeatureRecord] = []

    tcf_vendor_consents: List[TCFVendorConsentRecord] = []
    tcf_vendor_legitimate_interests: List[TCFVendorLegitimateInterestsRecord] = []
    tcf_vendor_relationships: List[TCFVendorRelationships] = []

    tcf_system_consents: List[TCFVendorConsentRecord] = []
    tcf_system_legitimate_interests: List[TCFVendorLegitimateInterestsRecord] = []
    tcf_system_relationships: List[TCFVendorRelationships] = []


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
            System.cookie_max_age_seconds.label("system_cookie_max_age_seconds"),
            System.uses_cookies.label("system_uses_cookies"),
            System.cookie_refresh.label("system_cookie_refresh"),
            System.uses_non_cookie_access.label("system_uses_non_cookie_access"),
            System.legitimate_interest_disclosure_url.label(
                "system_legitimate_interest_disclosure_url"
            ),
            System.privacy_policy.label("system_privacy_policy"),
            System.vendor_id,
            PrivacyDeclaration.data_use,
            PrivacyDeclaration.legal_basis_for_processing,
            PrivacyDeclaration.features,
            PrivacyDeclaration.retention_period,
        )
        .outerjoin(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
        .filter(
            or_(
                and_(
                    GVL_DATA_USE_FILTER,
                    PrivacyDeclaration.legal_basis_for_processing
                    == LegalBasisForProcessingEnum.CONSENT,
                ),
                and_(
                    GVL_DATA_USE_FILTER,
                    PrivacyDeclaration.legal_basis_for_processing
                    == LegalBasisForProcessingEnum.LEGITIMATE_INTEREST,
                    NOT_AC_SYSTEM_FILTER,
                ),
                AC_SYSTEM_NO_PRIVACY_DECL_FILTER,
            )
        )
        .order_by(
            PrivacyDeclaration.created_at.desc()
        )  # Order to get repeatable results when collapsing information
    )
    if not CONFIG.consent.ac_enabled:
        # If AC Mode is not enabled, exclude all Privacy Declarations tied to an AC-based system
        matching_privacy_declarations = matching_privacy_declarations.filter(
            NOT_AC_SYSTEM_FILTER
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
    for feature_name in record.features or []:
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
    retention_period: Optional[str],
    is_purpose_section: bool,
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

    if is_purpose_section:
        # Build the EmbeddedPurpose record with the retention period
        system_section.append(
            EmbeddedPurpose(  # type: ignore[arg-type]
                id=embedded_tcf_record.id,
                name=embedded_tcf_record.name,
                retention_period=retention_period,
            )
        )
    else:
        # Nest new cloned feature record beneath system otherwise
        system_section.append(embedded_tcf_record)


def _embed_system_under_purpose_or_feature(
    top_level_tcf_record: NonVendorRecord,
    non_vendor_record_map: Dict[int, NonVendorRecord],
    privacy_declaration_row: Row,
) -> None:
    """
    Embed system/vendor information beneath the corresponding top-level purpose or feature section.
    """

    vendor_id, system_identifier = get_system_identifiers(privacy_declaration_row)

    # Vendors when embedded beneath Purposes, Special Purposes, Features, or Special Features
    # are not separated by legal basis here -
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


def build_purpose_or_feature_section_and_update_vendor_map(
    relevant_uses_or_features: List[str],
    tcf_component_type: NonVendorSectionType,  # type: ignore[arg-type]
    tcf_vendor_component_type: VendorSectionType,
    vendor_subsection_name: str,
    vendor_map: Dict[
        str,
        VendorRecord,
    ],
    matching_privacy_declaration_query: Query,
) -> Tuple[Dict[int, NonVendorRecord], Dict[str, VendorRecord]]:
    """Builds a purpose or feature section of the TCF Overlay and makes corresponding updates to the vendor section

    Represents information in multiple formats.  Puts purposes and features at the top-level and embeds vendor and systems
    information underneath.  Likewise, puts vendor and system information top-level, and embeds purpose and feature information
    underneath.

    Vendor maps are passed in as an argument instead of being constructed here - in some places,
    the vendor map is modified multiple times each time this function is called.
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
            # Add top-level entry to the particular system section if applicable
            if system_identifier not in vendor_map:
                vendor_map[system_identifier] = tcf_vendor_component_type(
                    id=system_identifier,  # Identify system by vendor id if it exists, otherwise use system id.
                    name=privacy_declaration_row.system_name,
                    description=privacy_declaration_row.system_description,
                    has_vendor_id=bool(
                        vendor_id
                    ),  # Has_vendor_id will let us separate data between systems and vendors
                )

            # Embed the purpose/feature under the system if it doesn't exist
            _embed_purpose_or_feature_under_system(
                embedded_tcf_record=top_level_tcf_record.copy(),
                system_section=getattr(
                    vendor_map[system_identifier], vendor_subsection_name
                ),
                retention_period=privacy_declaration_row.retention_period,
                is_purpose_section=is_purpose_section,
            )

            # Finally, nest the system beneath this top level non-vendor tcf record
            _embed_system_under_purpose_or_feature(
                top_level_tcf_record=top_level_tcf_record,
                non_vendor_record_map=non_vendor_record_map,
                privacy_declaration_row=privacy_declaration_row,
            )

        # Separately, add AC Vendor to Vendor Consent Map if applicable
        add_ac_vendor_to_vendor_consent_map(
            vendor_map=vendor_map,
            tcf_vendor_component_type=tcf_vendor_component_type,
            privacy_declaration_row=privacy_declaration_row,
        )

    return non_vendor_record_map, vendor_map


def add_ac_vendor_to_vendor_consent_map(
    vendor_map: Dict[str, VendorRecord],
    tcf_vendor_component_type: VendorSectionType,
    privacy_declaration_row: Row,
) -> None:
    """
    Add systems with ac.*-prefixed vendor records to the Vendor Consent section if applicable.

    FE shows Consent toggle only for AC vendors, and they are not required to have Privacy Declarations
    """
    vendor_id, _ = get_system_identifiers(privacy_declaration_row)

    if not (vendor_id and vendor_id.startswith(AC_PREFIX)):
        return

    if not tcf_vendor_component_type == TCFVendorConsentRecord:
        return

    if vendor_id in vendor_map:
        return

    vendor_map[vendor_id] = TCFVendorConsentRecord(
        id=vendor_id,
        name=privacy_declaration_row.system_name,
        description=privacy_declaration_row.system_description,
        has_vendor_id=True,
    )


def populate_vendor_relationships_basic_attributes(
    vendor_map: Dict[str, TCFVendorRelationships],
    matching_privacy_declarations: Query,
) -> Dict[str, TCFVendorRelationships]:
    """Populates TCFVendorRelationships records for all vendors that we're displaying in the overlay.
    Ensures that these TCFVendorRelationships records have the "basic" TCF attributes populated.
    """
    for privacy_declaration_row in matching_privacy_declarations:
        vendor_id, system_identifier = get_system_identifiers(privacy_declaration_row)

        # Get the existing TCFVendorRelationships record or create a new one.
        # Add to the vendor map if it wasn't added in a previous section.
        vendor_relationship_record = vendor_map.get(system_identifier)
        if not vendor_relationship_record:
            vendor_relationship_record = TCFVendorRelationships(
                id=system_identifier,  # Identify system by vendor id if it exists, otherwise use system id.
                name=privacy_declaration_row.system_name,
                description=privacy_declaration_row.system_description,
                has_vendor_id=bool(
                    vendor_id  # This will let us separate data between systems and vendors later
                ),
            )
            vendor_map[system_identifier] = vendor_relationship_record

        # Now add basic attributes to the VendorRelationships record
        vendor_relationship_record.cookie_max_age_seconds = (
            privacy_declaration_row.system_cookie_max_age_seconds
        )
        vendor_relationship_record.uses_cookies = (
            privacy_declaration_row.system_uses_cookies
        )
        vendor_relationship_record.cookie_refresh = (
            privacy_declaration_row.system_cookie_refresh
        )
        vendor_relationship_record.uses_non_cookie_access = (
            privacy_declaration_row.system_uses_non_cookie_access
        )
        vendor_relationship_record.legitimate_interest_disclosure_url = (
            privacy_declaration_row.system_legitimate_interest_disclosure_url
        )
        vendor_relationship_record.privacy_policy_url = (
            privacy_declaration_row.system_privacy_policy
        )

    return vendor_map


def get_tcf_contents(
    db: Session,
) -> TCFExperienceContents:
    """
    Returns the base contents of the TCF overlay.

    Queries for systems/privacy declarations that have a relevant GVL data use and a legal basis of Consent or Legitimate interests,
    and builds the TCF Overlay from these systems and privacy declarations.

    TCF Overlay has Consent Purpose, Legitimate Interest Purpose, Special Purpose, Feature, and Special Feature Sections,
    that have relevant systems and vendors embedded underneath.

    We also have Consent Vendor, Legitimate Interests Vendor, and Vendor Relationships sections (same for systems),
    which are almost a reverse representation, and have their own purposes and features embedded underneath.

    """
    vendor_consent_map: Dict[str, TCFVendorConsentRecord] = {}
    vendor_legitimate_interests_map: Dict[str, TCFVendorLegitimateInterestsRecord] = {}
    vendor_relationships_map: Dict[str, TCFVendorRelationships] = {}

    matching_privacy_declarations: Query = get_matching_privacy_declarations(db)

    # Collect purposes with a legal basis of consent *or* AC systems (which aren't required to have privacy
    # declarations) and update system map
    (
        purpose_consent_map,
        updated_vendor_consent_map,
    ) = build_purpose_or_feature_section_and_update_vendor_map(
        PURPOSE_DATA_USES,
        tcf_component_type=TCFPurposeConsentRecord,
        tcf_vendor_component_type=TCFVendorConsentRecord,
        vendor_subsection_name="purpose_consents",
        vendor_map=vendor_consent_map,
        matching_privacy_declaration_query=matching_privacy_declarations.filter(
            or_(
                CONSENT_LEGAL_BASIS_FILTER,
                AC_SYSTEM_NO_PRIVACY_DECL_FILTER,
            )
        ),
    )

    # Collect purposes with a legal basis of legitimate interests and update system map
    (
        purpose_legitimate_interests_map,
        updated_vendor_legitimate_interests_map,
    ) = build_purpose_or_feature_section_and_update_vendor_map(
        PURPOSE_DATA_USES,
        tcf_component_type=TCFPurposeLegitimateInterestsRecord,
        tcf_vendor_component_type=TCFVendorLegitimateInterestsRecord,
        vendor_subsection_name="purpose_legitimate_interests",
        vendor_map=vendor_legitimate_interests_map,
        matching_privacy_declaration_query=matching_privacy_declarations.filter(
            LEGITIMATE_INTEREST_LEGAL_BASIS_FILTER
        ),
    )

    # Collect special purposes and update system map
    (
        special_purpose_map,
        updated_vendor_relationships_map,
    ) = build_purpose_or_feature_section_and_update_vendor_map(
        SPECIAL_PURPOSE_DATA_USES,
        tcf_component_type=TCFSpecialPurposeRecord,
        tcf_vendor_component_type=TCFVendorRelationships,
        vendor_subsection_name="special_purposes",
        vendor_map=vendor_relationships_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    # Collect features and update system map
    (
        feature_map,
        updated_vendor_relationships_map,
    ) = build_purpose_or_feature_section_and_update_vendor_map(
        [feature.name for feature in GVL_FEATURES.values()],
        tcf_component_type=TCFFeatureRecord,
        tcf_vendor_component_type=TCFVendorRelationships,
        vendor_subsection_name="features",
        vendor_map=updated_vendor_relationships_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    # Collect special features and update system map
    (
        special_feature_map,
        updated_vendor_relationships_map,
    ) = build_purpose_or_feature_section_and_update_vendor_map(
        [feature.name for feature in GVL_SPECIAL_FEATURES.values()],
        tcf_component_type=TCFSpecialFeatureRecord,
        tcf_vendor_component_type=TCFVendorRelationships,
        vendor_subsection_name="special_features",
        vendor_map=updated_vendor_relationships_map,
        matching_privacy_declaration_query=matching_privacy_declarations,
    )

    # Finally, add missing TCFVendorRelationships records for vendors that weren't already added
    # via the special_features, features, and special_purposes section.  Every vendor in the overlay
    # should show up in this section. Add the basic attributes to the vendor here to avoid duplication
    # in other vendor sections.
    updated_vendor_relationships_map = populate_vendor_relationships_basic_attributes(
        vendor_map=updated_vendor_relationships_map,
        matching_privacy_declarations=matching_privacy_declarations,
    )

    return combine_overlay_sections(
        purpose_consent_map,  # type: ignore[arg-type]
        purpose_legitimate_interests_map,  # type: ignore[arg-type]
        special_purpose_map,  # type: ignore[arg-type]
        feature_map,  # type: ignore[arg-type]
        special_feature_map,  # type: ignore[arg-type]
        updated_vendor_consent_map,  # type: ignore[arg-type]
        updated_vendor_legitimate_interests_map,  # type: ignore[arg-type]
        updated_vendor_relationships_map,  # type: ignore[arg-type]
    )


def combine_overlay_sections(
    purpose_consent_map: Dict[int, TCFPurposeConsentRecord],
    purpose_legitimate_interests_map: Dict[int, TCFPurposeLegitimateInterestsRecord],
    special_purpose_map: Dict[int, TCFSpecialPurposeRecord],
    feature_map: Dict[int, TCFFeatureRecord],
    special_feature_map: Dict[int, TCFSpecialFeatureRecord],
    updated_vendor_consent_map: Dict[str, TCFVendorConsentRecord],
    updated_vendor_legitimate_interests_map: Dict[
        str, TCFVendorLegitimateInterestsRecord
    ],
    updated_vendor_relationships: Dict[str, TCFVendorRelationships],
) -> TCFExperienceContents:
    """Combine the different TCF sections and sort purposes/features by id, and vendors/systems by name"""
    experience_contents = TCFExperienceContents()
    experience_contents.tcf_purpose_consents = _sort_by_id(purpose_consent_map)  # type: ignore[assignment]
    experience_contents.tcf_purpose_legitimate_interests = _sort_by_id(purpose_legitimate_interests_map)  # type: ignore[assignment]
    experience_contents.tcf_special_purposes = _sort_by_id(special_purpose_map)  # type: ignore[assignment]
    experience_contents.tcf_features = _sort_by_id(feature_map)  # type: ignore[assignment]
    experience_contents.tcf_special_features = _sort_by_id(special_feature_map)  # type: ignore[assignment]

    experience_contents.tcf_vendor_consents = []
    experience_contents.tcf_vendor_legitimate_interests = []
    experience_contents.tcf_vendor_relationships = []

    experience_contents.tcf_system_consents = []
    experience_contents.tcf_system_legitimate_interests = []
    experience_contents.tcf_system_relationships = []

    sorted_vendor_consents: List[TCFVendorConsentRecord] = _sort_by_name(updated_vendor_consent_map)  # type: ignore[assignment]
    sorted_vendor_legitimate_interests: List[TCFVendorLegitimateInterestsRecord] = _sort_by_name(updated_vendor_legitimate_interests_map)  # type: ignore[assignment]
    sorted_vendor_relationships: List[TCFVendorRelationships] = _sort_by_name(updated_vendor_relationships)  # type: ignore[assignment]

    for vendor in sorted_vendor_consents:
        vendor.purpose_consents.sort(key=lambda x: x.id)
        if vendor.has_vendor_id:
            experience_contents.tcf_vendor_consents.append(vendor)
        else:
            experience_contents.tcf_system_consents.append(vendor)

    for vendor in sorted_vendor_legitimate_interests:
        vendor.purpose_legitimate_interests.sort(key=lambda x: x.id)
        if vendor.has_vendor_id:
            experience_contents.tcf_vendor_legitimate_interests.append(vendor)
        else:
            experience_contents.tcf_system_legitimate_interests.append(vendor)

    for vendor in sorted_vendor_relationships:
        vendor.special_purposes.sort(key=lambda x: x.id)
        vendor.features.sort(key=lambda x: x.id)
        vendor.special_features.sort(key=lambda x: x.id)
        if vendor.has_vendor_id:
            experience_contents.tcf_vendor_relationships.append(vendor)
        else:
            experience_contents.tcf_system_relationships.append(vendor)

    return experience_contents


def _sort_by_id(
    tcf_mapping: Dict,
) -> SystemSubSections:
    return sorted(list(tcf_mapping.values()), key=lambda x: x.id)


def _sort_by_name(
    tcf_mapping: Dict,
) -> Union[
    List[TCFVendorConsentRecord],
    List[TCFVendorLegitimateInterestsRecord],
    List[TCFVendorRelationships],
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


def get_relevant_systems_for_tcf_attribute(  # pylint: disable=too-many-return-statements
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

    purpose_data_uses: List[str] = []
    if tcf_field in [
        TCFComponentType.purpose_consent.value,
        TCFComponentType.purpose_legitimate_interests.value,
        TCFComponentType.special_purpose.value,
    ]:
        purpose_data_uses = purpose_to_data_use(
            tcf_value, special_purpose="special" in tcf_field
        )

    if tcf_field == TCFComponentType.purpose_consent.value:
        return systems_that_match_tcf_data_uses(
            starting_privacy_declarations.filter(CONSENT_LEGAL_BASIS_FILTER),
            purpose_data_uses,
        )

    if tcf_field == TCFComponentType.purpose_legitimate_interests.value:
        return systems_that_match_tcf_data_uses(
            starting_privacy_declarations.filter(
                LEGITIMATE_INTEREST_LEGAL_BASIS_FILTER
            ),
            purpose_data_uses,
        )

    if tcf_field == TCFComponentType.special_purpose.value:
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

    if tcf_field == TCFComponentType.vendor_consent.value:
        return systems_that_match_vendor_string(
            starting_privacy_declarations.filter(
                or_(
                    CONSENT_LEGAL_BASIS_FILTER,
                    AC_SYSTEM_NO_PRIVACY_DECL_FILTER,
                )
            ),
            tcf_value,  # type: ignore[arg-type]
        )

    if tcf_field == TCFComponentType.vendor_legitimate_interests.value:
        return systems_that_match_vendor_string(
            starting_privacy_declarations.filter(
                LEGITIMATE_INTEREST_LEGAL_BASIS_FILTER
            ),
            tcf_value,  # type: ignore[arg-type]
        )

    if tcf_field == TCFComponentType.system_consent.value:
        return systems_that_match_system_id(
            starting_privacy_declarations.filter(CONSENT_LEGAL_BASIS_FILTER),
            tcf_value
            # type: ignore[arg-type]
        )

    if tcf_field == TCFComponentType.system_legitimate_interests.value:
        return systems_that_match_system_id(
            starting_privacy_declarations.filter(
                LEGITIMATE_INTEREST_LEGAL_BASIS_FILTER
            ),
            tcf_value,  # type: ignore[arg-type]
        )

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
