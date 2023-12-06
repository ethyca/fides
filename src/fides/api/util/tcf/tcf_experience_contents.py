# mypy: disable-error-code="arg-type, attr-defined, assignment"
from enum import Enum
from typing import Dict, List, Optional, Tuple

from fideslang.gvl import MAPPED_PURPOSES, MAPPED_SPECIAL_PURPOSES
from fideslang.models import LegalBasisForProcessingEnum
from sqlalchemy import and_, case, not_, or_
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Alias
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    PrivacyDeclaration,
    System,
)
from fides.api.models.tcf_purpose_overrides import TCFPurposeOverride
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.tcf import (
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

AC_PREFIX = "gacp."
GVL_PREFIX = "gvl."

PURPOSE_DATA_USES: List[str] = []
for purpose in MAPPED_PURPOSES.values():
    PURPOSE_DATA_USES.extend(purpose.data_uses)

SPECIAL_PURPOSE_DATA_USES: List[str] = []
for special_purpose in MAPPED_SPECIAL_PURPOSES.values():
    SPECIAL_PURPOSE_DATA_USES.extend(special_purpose.data_uses)

ALL_GVL_DATA_USES = list(set(PURPOSE_DATA_USES) | set(SPECIAL_PURPOSE_DATA_USES))

# Common SQLAlchemy filters used below

# Define a special-case filter for AC Systems with no Privacy Declarations
AC_SYSTEM_NO_PRIVACY_DECL_FILTER: BooleanClauseList = and_(
    System.vendor_id.startswith(AC_PREFIX), PrivacyDeclaration.id.is_(None)
)

# Filter for any non-AC Systems
NOT_AC_SYSTEM_FILTER: BooleanClauseList = or_(
    not_(System.vendor_id.startswith(AC_PREFIX)), System.vendor_id.is_(None)
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


def get_legal_basis_override_subquery(db: Session) -> Alias:
    """Subquery that allows us to globally override a purpose's legal basis for processing.

    Original legal basis for processing is returned where:
    - feature is disabled
    - declaration's legal basis is not flexible
    - no legal basis override specified

    Null is returned where:
    - Purpose is excluded (this will effectively remove the purpose from the Experience)

    Otherwise, we return the override!
    """
    if not CONFIG.consent.override_vendor_purposes:
        return db.query(
            PrivacyDeclaration.id,
            PrivacyDeclaration.legal_basis_for_processing.label(
                "overridden_legal_basis_for_processing"
            ),
        ).subquery()

    return (
        db.query(
            PrivacyDeclaration.id,
            case(
                [
                    (
                        PrivacyDeclaration.flexible_legal_basis_for_processing.is_(
                            False
                        ),
                        PrivacyDeclaration.legal_basis_for_processing,
                    ),
                    (
                        TCFPurposeOverride.is_included.is_(False),
                        None,
                    ),
                    (
                        TCFPurposeOverride.required_legal_basis.is_(None),
                        PrivacyDeclaration.legal_basis_for_processing,
                    ),
                ],
                else_=TCFPurposeOverride.required_legal_basis,
            ).label("overridden_legal_basis_for_processing"),
        )
        .outerjoin(
            TCFPurposeOverride,
            TCFPurposeOverride.purpose == PrivacyDeclaration.purpose,
        )
        .subquery()
    )


def get_tcf_base_query_and_filters(
    db: Session,
) -> Tuple[Query, BinaryExpression, BinaryExpression]:
    """
    Returns the base query that contains the foundations of the TCF Experience as well as
    two filters to further refine the query when building the Experience.

    Rows show up corresponding to systems with GVL data uses and Legal bases of Consent or Legitimate interests.
    AC systems are also included here.
    Purpose overrides are applied at this stage which may suppress purposes or toggle the legal basis.
    """
    legal_basis_override_subquery = get_legal_basis_override_subquery(db)

    consent_legal_basis_filter: BinaryExpression = (
        legal_basis_override_subquery.c.overridden_legal_basis_for_processing
        == LegalBasisForProcessingEnum.CONSENT
    )
    legitimate_interest_legal_basis_filter: BinaryExpression = (
        legal_basis_override_subquery.c.overridden_legal_basis_for_processing
        == LegalBasisForProcessingEnum.LEGITIMATE_INTEREST
    )

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
            legal_basis_override_subquery.c.overridden_legal_basis_for_processing.label(  # pylint: disable=no-member
                "legal_basis_for_processing"
            ),
            PrivacyDeclaration.features,
            PrivacyDeclaration.retention_period,
            PrivacyDeclaration.purpose,
            PrivacyDeclaration.legal_basis_for_processing.label(
                "original_legal_basis_for_processing"
            ),
        )
        .outerjoin(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
        .outerjoin(
            legal_basis_override_subquery,
            legal_basis_override_subquery.c.id == PrivacyDeclaration.id,
        )
        .filter(
            or_(
                and_(GVL_DATA_USE_FILTER, consent_legal_basis_filter),
                and_(
                    GVL_DATA_USE_FILTER,
                    legitimate_interest_legal_basis_filter,
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

    return (
        matching_privacy_declarations,
        consent_legal_basis_filter,
        legitimate_interest_legal_basis_filter,
    )
