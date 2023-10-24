import hashlib
import json
from typing import Dict, List, Union

from pydantic import Extra, Field, root_validator

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_experience import ExperienceMeta
from fides.api.schemas.tcf import (
    TCFVendorConsentRecord,
    TCFVendorLegitimateInterestsRecord,
    TCMobileData,
)
from fides.api.util.tcf.fides_string import build_fides_string
from fides.api.util.tcf.tc_mobile_data import build_tc_data_for_mobile
from fides.api.util.tcf.tc_model import TCModel, convert_tcf_contents_to_tc_model
from fides.api.util.tcf.tcf_experience_contents import TCFExperienceContents


class TCFVersionHash(FidesSchema):
    """Minimal subset of the TCF experience details that capture when consent should be resurfaced

    These values are later hashed, and you can treat a change in a hash as a trigger for re-establishing
    transparency and consent
    """

    policy_version: int = Field(
        description="TCF Policy Version. A new policy version invalidates existing strings and requires CMPs to "
        "re-establish transparency and consent from users."
    )
    vendor_purpose_consents: List[str] = Field(
        description="Stores vendor * purpose * consent legal basis in the format: "
        "<universal_vendor_id>-<comma separated purposes>"
    )
    vendor_purpose_legitimate_interests: List[str] = Field(
        description="Stores vendor * purpose * legitimate interest legal basis in the format: "
        "<universal_vendor_id>-<comma separated purposes>"
    )
    gvl_vendors_disclosed: List[int] = Field(
        description="List of GVL vendors disclosed from the current vendor list"
    )

    @root_validator()
    @classmethod
    def sort_lists(cls, values: Dict) -> Dict:
        """Verify lists are sorted deterministically for repeatability"""
        for field, val in values.items():
            if isinstance(val, list):
                values[field] = sorted(val)
        return values

    class Config:
        extra = Extra.ignore


def _build_tcf_version_hash_model(
    tcf_contents: TCFExperienceContents,
) -> TCFVersionHash:
    """Given tcf_contents, constructs the TCFVersionHash model containing
    the raw contents to build the `version_hash` for the TCF Experience.

    Builds a model that assumes the customer has *opted in* to all preferences, to
    get the maximum possible number of attributes added to our hash for the current
    system configuration.
    """

    def build_vendor_by_purpose_strings(
        vendor_list: Union[
            List[TCFVendorConsentRecord], List[TCFVendorLegitimateInterestsRecord]
        ]
    ) -> List[str]:
        """Hash helper for building vendor x purposes.  Converts a list of vendor records
        into a list of strings each consisting of a vendor id, a separator (-), and comma
        separated purposes (if applicable) with the given legal basis.

        Example:
        [<universal_vendor_id>-<comma separated purposes>]
        ["gacp.100", "gvl.8-1,2,3", "gvl.56-3,4,5]
        """
        vendor_by_purpose_lists: List[str] = []
        for vendor_record in vendor_list:
            vendor_id: str = vendor_record.id
            purposes_key: str = (
                "purpose_consents"
                if isinstance(vendor_record, TCFVendorConsentRecord)
                else "purpose_legitimate_interests"
            )
            purpose_ids = sorted(
                purpose_record.id
                for purpose_record in getattr(vendor_record, purposes_key)
            )
            concatenated_purposes_string: str = ",".join(
                str(purpose_id) for purpose_id in purpose_ids
            )
            vendor_by_purpose_lists.append(
                vendor_id + "-" + concatenated_purposes_string
                if concatenated_purposes_string
                else vendor_id
            )
        return vendor_by_purpose_lists

    vendor_consents: List[str] = build_vendor_by_purpose_strings(
        tcf_contents.tcf_vendor_consents + tcf_contents.tcf_system_consents
    )
    vendor_li: List[str] = build_vendor_by_purpose_strings(
        tcf_contents.tcf_vendor_legitimate_interests
        + tcf_contents.tcf_system_legitimate_interests
    )

    # Building the TC model to pull off the GVL Policy version and get vendors_disclosed
    # which is a component of the TC string.
    model: TCModel = convert_tcf_contents_to_tc_model(
        tcf_contents, UserConsentPreference.opt_in
    )

    return TCFVersionHash(
        policy_version=model.policy_version,
        vendor_purpose_consents=vendor_consents,
        vendor_purpose_legitimate_interests=vendor_li,
        gvl_vendors_disclosed=model.vendors_disclosed,  # `vendors_disclosed` field only has GVL vendors present
        # in "current" GVL vendor list
    )


def build_tcf_version_hash(tcf_contents: TCFExperienceContents) -> str:
    """Returns a 12-character version hash of the TCF Experience that changes when consent should be recollected.

    Changes when:
      - New GVL, AC Vendor, or "other" vendor is added to TCF Experience
      - Existing vendor adds a new TCF purpose
      - Existing vendor changes the legal basis for a previously-disclosed purpose
      - TCF Policy version changes
      - Vendor moves from AC to GVL
      - Vendor moves from GVL 2 to GVL 3
    """
    tcf_version_hash_model: TCFVersionHash = _build_tcf_version_hash_model(tcf_contents)
    json_str: str = json.dumps(tcf_version_hash_model.dict(), sort_keys=True)
    hashed_val: str = hashlib.sha256(json_str.encode()).hexdigest()
    return hashed_val[:12]  # Shortening string for usability, collision risk is low


def build_experience_tcf_meta(tcf_contents: TCFExperienceContents) -> Dict:
    """Build TCF Meta information to supplement a TCF Privacy Experience at runtime"""

    accept_all_tc_model: TCModel = convert_tcf_contents_to_tc_model(
        tcf_contents, UserConsentPreference.opt_in
    )
    reject_all_tc_model: TCModel = convert_tcf_contents_to_tc_model(
        tcf_contents, UserConsentPreference.opt_out
    )

    accept_all_mobile_data: TCMobileData = build_tc_data_for_mobile(accept_all_tc_model)
    reject_all_mobile_data: TCMobileData = build_tc_data_for_mobile(reject_all_tc_model)

    return ExperienceMeta(
        version_hash=build_tcf_version_hash(tcf_contents),
        accept_all_fides_string=build_fides_string(
            accept_all_mobile_data.IABTCF_TCString,
            accept_all_mobile_data.IABTCF_AddtlConsent,
        ),
        reject_all_fides_string=build_fides_string(
            reject_all_mobile_data.IABTCF_TCString,
            reject_all_mobile_data.IABTCF_AddtlConsent,
        ),
        accept_all_fides_mobile_data=accept_all_mobile_data,
        reject_all_fides_mobile_data=reject_all_mobile_data,
    ).dict()
