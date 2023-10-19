import hashlib
import json
from typing import Dict, List

from pydantic import Extra, root_validator

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_experience import ExperienceMeta
from fides.api.schemas.tcf import TCMobileData
from fides.api.util.tcf.tc_mobile_data import build_tc_data_for_mobile
from fides.api.util.tcf.tc_model import TCModel, convert_tcf_contents_to_tc_model
from fides.api.util.tcf.tcf_experience_contents import TCFExperienceContents


class TCFVersionHash(FidesSchema):
    """Minimal subset of the TCF experience details that capture when consent should be resurfaced"""

    policy_version: int
    purpose_consents: List[int]
    purpose_legitimate_interests: List[int]
    special_feature_optins: List[int]
    vendor_consents: List[int]
    vendor_legitimate_interests: List[int]

    @root_validator()
    @classmethod
    def sort_lists(cls, values: Dict) -> Dict:
        """Verify lists are sorted ascending for repeatability"""
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
    model: TCModel = convert_tcf_contents_to_tc_model(
        tcf_contents, UserConsentPreference.opt_in
    )
    return TCFVersionHash(**model.dict())


def build_tcf_version_hash(tcf_contents: TCFExperienceContents) -> str:
    """Returns a 12-character version hash for TCF that should only change
    if there are updates to vendors, purposes, and special features sections or legal basis.

    This hash can be used to determine if the TCF Experience needs to be resurfaced to the customer,
    because the experience has changed in a meaningful way.
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
        accept_all_fides_string=accept_all_mobile_data.IABTCF_TCString,
        reject_all_fides_string=reject_all_mobile_data.IABTCF_TCString,
        accept_all_fides_mobile_data=accept_all_mobile_data,
        reject_all_fides_mobile_data=reject_all_mobile_data,
    ).dict()
