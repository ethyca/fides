from functools import lru_cache
from os.path import dirname, join
from typing import List, Tuple

import yaml
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.privacy_experience import ComponentType, PrivacyExperience
from fides.api.models.privacy_notice import PrivacyNoticeRegion
from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.schemas.privacy_notice import TCFConsentRecord, TCFVendorConsentRecord
from fides.config.helpers import load_file

TCF_PATH = join(
    dirname(__file__),
    "../../data/privacy_notices",
    "tcf.yml",
)


@lru_cache(maxsize=1)
def load_tcf_data_uses(
    db,
) -> Tuple[List[TCFConsentRecord], List[TCFVendorConsentRecord]]:
    with open(load_file([TCF_PATH]), "r", encoding="utf-8") as file:
        raw_tcf_data_uses = yaml.safe_load(file).get("tcf_data_uses", [])

    system_data_uses: set[str] = System.get_data_uses(
        System.all(db), include_parents=True
    )

    relevant_data_uses = system_data_uses.intersection(
        set([record["key"] for record in raw_tcf_data_uses])
    )

    if not relevant_data_uses:
        return [], []

    systems = (
        db.query(System)
        .join(
            PrivacyDeclaration,
            PrivacyDeclaration.system_id == System.id,
        )
        .filter(PrivacyDeclaration.data_use.in_(relevant_data_uses))
    )

    data_use_records = [
        TCFConsentRecord(**record)
        for record in raw_tcf_data_uses
        if record["key"] in relevant_data_uses
    ]
    vendors = []
    for system in systems:
        for connection in system.connection_configs.filter(
            db, conditions=(ConnectionConfig.system_id == system.id)
        ):
            if (
                connection.connection_type == ConnectionType.saas
                and connection.saas_config.get("type")
            ):
                vendor_consent_record = TCFVendorConsentRecord(
                    **{"key": connection.saas_config.get("type")}
                )
                individual_system_data_uses = System.get_data_uses(
                    [system], include_parents=True
                )
                relevant_system_data_uses = [
                    use
                    for use in individual_system_data_uses
                    if use in relevant_data_uses
                ]
                for record in raw_tcf_data_uses:
                    if record["key"] in relevant_system_data_uses:
                        vendor_consent_record.data_uses.append(
                            TCFConsentRecord(**record)
                        )
                vendors.append(vendor_consent_record)
    return data_use_records, vendors


EEA_COUNTRIES = [
    PrivacyNoticeRegion.be,
    PrivacyNoticeRegion.bg,
    PrivacyNoticeRegion.cz,
    PrivacyNoticeRegion.dk,
    PrivacyNoticeRegion.de,
    PrivacyNoticeRegion.ee,
    PrivacyNoticeRegion.ie,
    PrivacyNoticeRegion.gr,
    PrivacyNoticeRegion.es,
    PrivacyNoticeRegion.fr,
    PrivacyNoticeRegion.hr,
    PrivacyNoticeRegion.it,
    PrivacyNoticeRegion.cy,
    PrivacyNoticeRegion.lv,
    PrivacyNoticeRegion.lv,
    PrivacyNoticeRegion.lt,
    PrivacyNoticeRegion.lu,
    PrivacyNoticeRegion.hu,
    PrivacyNoticeRegion.mt,
    PrivacyNoticeRegion.nl,
    PrivacyNoticeRegion.at,
    PrivacyNoticeRegion.pl,
    PrivacyNoticeRegion.pt,
    PrivacyNoticeRegion.ro,
    PrivacyNoticeRegion.si,
    PrivacyNoticeRegion.sk,
    PrivacyNoticeRegion.fi,
    PrivacyNoticeRegion.se,
    PrivacyNoticeRegion.gb_eng,
    PrivacyNoticeRegion.gb_sct,
    PrivacyNoticeRegion.gb_wls,
    PrivacyNoticeRegion.gb_nir,
    PrivacyNoticeRegion.no,
    "is",
    PrivacyNoticeRegion.li,
]


def create_tcf_experiences_on_startup(db: Session):
    for region in EEA_COUNTRIES:
        if not PrivacyExperience.get_experience_by_region_and_component(
            db, region, ComponentType.tcf_overlay
        ):
            PrivacyExperience.create_default_experience_for_region(
                db, region, ComponentType.tcf_overlay
            )
