import hashlib
import json
from typing import Dict

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.privacy_experience import ExperienceMeta
from fides.api.util.tcf.tc_mobile_data import build_tc_data_for_mobile
from fides.api.util.tcf.tc_model import TCFVersionHash, TCModel, build_tc_model
from fides.api.util.tcf.tc_string import build_tc_string
from fides.api.util.tcf_util import TCFExperienceContents


def _build_tcf_version_hash_model(
    tcf_contents: TCFExperienceContents,
) -> TCFVersionHash:
    """Given tcf_contents, constructs the TCFVersionHash model containing
    the raw contents to build the version_hash"""
    model: TCModel = build_tc_model(tcf_contents, UserConsentPreference.opt_in)
    return TCFVersionHash(**model.dict())


def build_tcf_version_hash(tcf_contents: TCFExperienceContents) -> str:
    """Returns a 12-character version hash for TCF that should only change
    if there are updates to vendors, purposes, and special features sections or legal basis.
    """
    tcf_version_hash_model: TCFVersionHash = _build_tcf_version_hash_model(tcf_contents)
    json_str: str = json.dumps(tcf_version_hash_model.dict(), sort_keys=True)
    hashed_val: str = hashlib.sha256(json_str.encode()).hexdigest()
    return hashed_val[:12]  # Shortening string for usability, collision risk is low


def build_experience_tcf_meta(tcf_contents: TCFExperienceContents) -> Dict:
    """Build TCF Meta information to supplement a TCF Privacy Experience"""

    accept_all_tc_model: TCModel = build_tc_model(
        tcf_contents, UserConsentPreference.opt_in
    )
    reject_all_tc_model: TCModel = build_tc_model(
        tcf_contents, UserConsentPreference.opt_out
    )

    return ExperienceMeta(
        version_hash=build_tcf_version_hash(tcf_contents),
        accept_all_tc_string=build_tc_string(accept_all_tc_model),
        reject_all_tc_string=build_tc_string(reject_all_tc_model),
        accept_all_tc_mobile_data=build_tc_data_for_mobile(accept_all_tc_model),
        reject_all_tc_mobile_data=build_tc_data_for_mobile(reject_all_tc_model),
    ).dict()
