from functools import lru_cache
from os.path import dirname, join
from typing import Dict, List, Set, Tuple

import yaml
from sqlalchemy import or_
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


@lru_cache()
def load_tcf_data_uses(
    db,
) -> Tuple[List[TCFConsentRecord], List[TCFVendorConsentRecord]]:
    """
    Load TCF Data uses from TCF_PATH and then return data uses that are parents/exact matches
    of data uses on systems, and vendors that contain these data uses.
    """
    with open(load_file([TCF_PATH]), "r", encoding="utf-8") as file:
        raw_tcf_data_uses = yaml.safe_load(file).get("tcf_data_uses", [])

    system_data_uses: set[str] = System.get_data_uses(
        System.all(db), include_parents=True
    )

    relevant_data_uses: set[str] = system_data_uses.intersection(
        {record["id"] for record in raw_tcf_data_uses}
    )

    if not relevant_data_uses:
        return [], []

    systems = (
        db.query(System, PrivacyDeclaration)
        .join(
            PrivacyDeclaration,
            PrivacyDeclaration.system_id == System.id,
        )
        .filter(
            or_(
                *[
                    PrivacyDeclaration.data_use.like(data_use_parent + "%")
                    for data_use_parent in relevant_data_uses
                ]
            )
        )
    )

    system_map: Dict[str, TCFVendorConsentRecord] = {}

    for system, privacy_declaration in systems:
        if not system.connection_configs:
            continue

        if system.id not in system_map:
            for connection in system.connection_configs.filter(
                db, conditions=(ConnectionConfig.system_id == system.id)
            ):
                if (
                    connection.connection_type == ConnectionType.saas
                    and connection.saas_config.get("type")
                ):
                    system_map[system.id] = TCFVendorConsentRecord(
                        **{"id": connection.saas_config.get("type")}
                    )

        for record in raw_tcf_data_uses:
            if privacy_declaration.data_use.startswith(record["id"]) and record[
                "id"
            ] not in [use.id for use in system_map[system.id].data_uses]:
                system_map[system.id].data_uses.append(TCFConsentRecord(**record))

    return [
        TCFConsentRecord(**record)
        for record in raw_tcf_data_uses
        if record["id"] in relevant_data_uses
    ], list(system_map.values())


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
