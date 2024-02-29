"""system dictionary data migration

Revision ID: fd52d5f08c17
Revises: 39397820a0d5
Create Date: 2023-08-04 14:14:32.421414

"""

import json
from typing import Any, Dict, List, Optional, Tuple

from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.sql.elements import TextClause

from fides.config import CONFIG

revision = "fd52d5f08c17"
down_revision = "39397820a0d5"
branch_labels = None
depends_on = None

JOINT_CONTROLLER_INFO = "joint_controller_info"
DOES_INTERNATIONAL_TRANSFERS = "does_international_transfers"
RESPONSIBILITY = "responsibility"
REQUIRES_DATA_PROTECTION_ASSESSMENTS = "requires_data_protection_assessments"
DPA_LOCATION = "dpa_location"
DPA_PROGRESS = "dpa_progress"

LEGAL_BASIS_FOR_PROCESSING = "legal_basis_for_processing"
IMPACT_ASSESSMENT_LOCATION = "impact_assessment_location"
PROCESSES_SPECIAL_CATEGORY_DATA = "processes_special_category_data"
SPECIAL_CATEGORY_LEGAL_BASIS = "special_category_legal_basis"
DATA_SHARED_WITH_THIRD_PARTIES = "data_shared_with_third_parties"
THIRD_PARTIES = "third_parties"
RETENTION_PERIOD = "retention_period"


def _system_transform_joint_controller_info(
    joint_controller_decrypted: Optional[Dict],
    datasets_joint_controller_decrypted: List[Optional[Dict]],
) -> Optional[str]:
    """Migrating systems.joint_controller and datasets.joint_controller encrypted json string fields to
    System.joint_controller_info which is just a string.

    Prioritizing system joint_controller info if it exists, or taking the first non-null entry from datasets
    otherwise.
    """
    new_joint_controller_info: Optional[str] = None
    # Prioritize system data over dataset data
    joint_controller_data = (
        joint_controller_decrypted
        or next(  # Multiple datasets can be related to a system, so we use the first non null one if applicable
            (
                item
                for item in datasets_joint_controller_decrypted or []
                if item is not None
            ),
            None,
        )
    )
    if joint_controller_data and isinstance(joint_controller_data, dict):
        separated_fields = [
            joint_controller_data.get("name"),
            joint_controller_data.get("address"),
            joint_controller_data.get("email"),
            joint_controller_data.get("phone"),
        ]

        # If data looks like {"name": "N/A", "address": "N/A"...}, return None instead of an empty string
        new_joint_controller_info = (
            "; ".join([elem for elem in separated_fields if elem and elem != "N/A"])
            or None
        )

    return new_joint_controller_info


def _system_calculate_does_international_transfers(
    system_third_country_transfers: Optional[List[str]],
    dataset_third_country_transfers: Optional[List[str]],
) -> bool:
    """Migrating System.third_country_transfers and Dataset.third_country_transfers to System.does_international_transfers
    If any countries are listed, regardless of which country it is, System.does_international_transfers will be set to true.
    """
    return any([system_third_country_transfers, dataset_third_country_transfers])


def _system_transform_data_responsibility_title_type(
    dept_str: Optional[str],
) -> List[str]:
    """Migrating System.data_responsibility_title (str) to System.responsibility(list).  There can now be potentially many
    items listed here"""
    return [dept_str] if dept_str else []


def _flatten_data_protection_impact_assessment(
    data_protection_impact_assessment: Optional[Dict],
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Flattening data from System.data_protection_impact_assessment into three separate fields:
    System.requires_data_protection_assessments, System.dpa_location, and System.dpa_progress
    """
    if not data_protection_impact_assessment or not isinstance(
        data_protection_impact_assessment, dict
    ):
        return False, None, None

    requires_data_protection_assessments = data_protection_impact_assessment.get(
        "is_required", False
    )
    dpa_progress = data_protection_impact_assessment.get("progress")
    dpa_location = data_protection_impact_assessment.get("link")
    return requires_data_protection_assessments, dpa_progress, dpa_location


def system_dictionary_additive_migration(bind: Connection):
    """Copy and/or transform existing data in Datasets, PrivacyDeclarations and the System itself to new
    Systems fields to support dictionary work"""
    get_systems_query: TextClause = text(
        """
        SELECT 
            ctl_systems.id,
            pgp_sym_decrypt(ctl_systems.joint_controller::bytea, :encryption_key) AS joint_controller_decrypted,
            ctl_systems.third_country_transfers,
            ctl_systems.data_responsibility_title,
            ctl_systems.data_protection_impact_assessment,
            array_accum(ctl_datasets.third_country_transfers) as dataset_third_country_transfers,
            array_agg(pgp_sym_decrypt(ctl_datasets.joint_controller::bytea, :encryption_key)) AS datasets_joint_controller_decrypted
        FROM ctl_systems
        LEFT JOIN privacydeclaration ON ctl_systems.id = privacydeclaration.system_id 
        LEFT JOIN ctl_datasets ON ctl_datasets.fides_key = ANY(privacydeclaration.dataset_references) 
        GROUP BY ctl_systems.id
        """
    )
    for row in bind.execute(
        get_systems_query, {"encryption_key": CONFIG.user.encryption_key}
    ):
        (
            requires_data_protection_assessments,
            dpa_progress,
            dpa_location,
        ) = _flatten_data_protection_impact_assessment(
            row["data_protection_impact_assessment"]
        )

        system_joint_controller_data: Optional[Dict] = json.loads(
            row["joint_controller_decrypted"] or "null"
        )
        # Potentially multiple datasets on systems that have joint controller info
        datasets_joint_controller_data: List[Optional[Dict]] = [
            json.loads(item)
            for item in row["datasets_joint_controller_decrypted"] or "null"
            if item
        ]

        system_data = {
            JOINT_CONTROLLER_INFO: _system_transform_joint_controller_info(
                system_joint_controller_data, datasets_joint_controller_data
            ),  # System.joint_controller_info populated from flattened data from either System.joint_controller
            # or Datasets.joint_controller. New field is not as rigid
            DOES_INTERNATIONAL_TRANSFERS: _system_calculate_does_international_transfers(
                row["third_country_transfers"], row["dataset_third_country_transfers"]
            ),  # System.does_international_transfers is populated based on whether System.third_country_transfers
            # or Dataset.third_country_transfers exist
            RESPONSIBILITY: _system_transform_data_responsibility_title_type(
                row[
                    "data_responsibility_title"
                ]  # From System.data_responsibility_title
            ),
            REQUIRES_DATA_PROTECTION_ASSESSMENTS: requires_data_protection_assessments,  # From System.data_protection_impact_assessment
            DPA_LOCATION: dpa_location,  # From System.data_protection_impact_assessment
            DPA_PROGRESS: dpa_progress,  # From System.data_protection_impact_assessment
        }

        update_system_query: TextClause = text(
            """
                UPDATE ctl_systems
                SET 
                    joint_controller_info = :joint_controller_info,
                    does_international_transfers = :does_international_transfers,
                    responsibility = :responsibility,
                    requires_data_protection_assessments = :requires_data_protection_assessments,
                    dpa_location = :dpa_location,
                    dpa_progress = :dpa_progress
                WHERE id = :id;
            """
        )

        system_data: Dict[str, Any] = system_data
        bind.execute(
            update_system_query,
            {"id": row["id"], **system_data},
        )


# Casing is changing
legal_basis_for_processing_map: Dict = {
    "Consent": "Consent",
    "Contract": "Contract",
    "Legal Obligation": "Legal obligations",
    "Legal obligations": "Legal obligations",
    "Vital Interest": "Vital interests",
    "Vital interests": "Vital interests",
    "Public Interest": "Public interest",
    "Legitimate Interests": "Legitimate interests",
    "Legitimate interests": "Legitimate interests",
}

# Language/casing is changing
special_category_map: Dict = {
    "Consent": "Explicit consent",
    "Employment": "Employment, social security and social protection",
    "Vital Interests": "Vital interests",
    "Non-profit Bodies": "Not-for-profit bodies",
    "Public by Data Subject": "Made public by the data subject",
    "Legal Claims": "Legal claims or judicial acts",
    "Substantial Public Interest": "Reasons of substantial public interest (with a basis in law)",
    "Medical": "Health or social care (with a basis in law)",
    "Public Health Interest": "Public health (with a basis in law)",
}


def _get_privacy_declaration_legal_basis_for_processing(
    data_use_legal_basis: Optional[str],
    legitimate_interest_impact_assessment: Optional[str],
) -> Optional[str]:
    """Use DataUse.legal_basis or DataUse.legitimate_interest_impact_assessment to set the value of
    PrivacyDeclaration.legal_basis_for_processing"""
    if legitimate_interest_impact_assessment:
        return "Legitimate interests"
    if data_use_legal_basis:
        return legal_basis_for_processing_map.get(data_use_legal_basis, None)
    return None


def _get_third_party_data(
    recipients: Optional[List[str]],
) -> Tuple[bool, Optional[str]]:
    """Migrate data from DataUse.recipients field to new PrivacyDeclaration.third_parties and
    PrivacyDeclaration.data_shared_with_third_parties be true
    """
    data_shared_with_third_parties: bool = bool(recipients)
    third_parties: Optional[str] = None

    if isinstance(recipients, list):
        third_parties = "; ".join([elem for elem in recipients if elem]) or None

    return data_shared_with_third_parties, third_parties


def _get_retention_period(
    retention_periods: Optional[List[str]],
) -> str:
    """Migrate data from Dataset.retention field all related PrivacyDeclaration.retention_periods"""
    if not retention_periods:
        return "No retention or erasure policy"

    for retention_period in retention_periods:
        # There may be multiple datasets associated with a privacy declaration.  Choosing the first retention
        # period that does not equal "No retention or erasure policy" if applicable.
        if (
            retention_period is not None
            and retention_period != "No retention or erasure policy"
        ):
            return retention_period
    return "No retention or erasure policy"


def privacy_declaration_additive_migration(bind: Connection):
    """Copy/transform existing data from DataUse and Datasets fields to new Privacy Declaration fields"""
    all_privacy_declarations: Dict[str, Dict] = {}

    # Selecting relevant DataUse fields to move over to PrivacyDeclaration
    get_privacy_declarations_query: TextClause = text(
        """
        SELECT 
            privacydeclaration.id,
            ctl_data_uses.legal_basis,
            ctl_data_uses.legitimate_interest_impact_assessment,
            ctl_data_uses.special_category,
            ctl_data_uses.recipients
        FROM privacydeclaration
        LEFT JOIN ctl_data_uses ON privacydeclaration.data_use = ctl_data_uses.fides_key;
        """
    )
    for row in bind.execute(get_privacy_declarations_query):
        data_shared_with_third_parties, third_parties = _get_third_party_data(
            row["recipients"]
        )

        privacy_declaration_data = {
            LEGAL_BASIS_FOR_PROCESSING: _get_privacy_declaration_legal_basis_for_processing(
                row["legal_basis"], row["legitimate_interest_impact_assessment"]
            ),
            IMPACT_ASSESSMENT_LOCATION: row["legitimate_interest_impact_assessment"],
            PROCESSES_SPECIAL_CATEGORY_DATA: bool(row["special_category"]),
            SPECIAL_CATEGORY_LEGAL_BASIS: special_category_map.get(
                row["special_category"], None
            ),
            DATA_SHARED_WITH_THIRD_PARTIES: data_shared_with_third_parties,
            THIRD_PARTIES: third_parties,
        }

        all_privacy_declarations[row["id"]] = privacy_declaration_data

    # Select first retention periods from associated datasets to migrate over to PrivacyDeclaration
    data_retention_query: TextClause = text(
        """
        SELECT 
            privacydeclaration.id,
            array_agg(ctl_datasets.retention) as retention_periods
        FROM privacydeclaration
        LEFT JOIN ctl_datasets ON ctl_datasets.fides_key = ANY(privacydeclaration.dataset_references)
        GROUP BY privacydeclaration.id;
        """
    )

    for row in bind.execute(data_retention_query):
        all_privacy_declarations[row["id"]][RETENTION_PERIOD] = _get_retention_period(
            row["retention_periods"]
        )

    for privacy_declaration_id, update_data in all_privacy_declarations.items():
        update_privacy_declarations_query: TextClause = text(
            """
                UPDATE privacydeclaration
                SET 
                    legal_basis_for_processing = :legal_basis_for_processing,
                    impact_assessment_location = :impact_assessment_location,
                    processes_special_category_data = :processes_special_category_data,
                    special_category_legal_basis = :special_category_legal_basis,
                    data_shared_with_third_parties = :data_shared_with_third_parties,
                    third_parties = :third_parties,
                    retention_period = :retention_period
                WHERE id = :id;
            """
        )

        bind.execute(
            update_privacy_declarations_query,
            {
                "id": privacy_declaration_id,
                **update_data,
            },
        )


def upgrade():
    bind: Connection = op.get_bind()

    result = bind.execute("SHOW server_version;")  # 12.16 (Debian 12.16-1.pgdg120+1)
    version = result.fetchone()[0]
    major_version = int(version.split(".")[0])

    # Add a new function to be able to combine potentially multiple arrays of different sizes alongside null values
    # into a single array
    if major_version >= 14:
        bind.execute(text("DROP AGGREGATE IF EXISTS array_accum(anycompatiblearray);"))
        bind.execute(
            text(
                """
                CREATE AGGREGATE array_accum (anycompatiblearray)
                (
                    sfunc = array_cat,
                    stype = anycompatiblearray,
                    initcond = '{}'
                );  
                """
            )
        )
    else:
        bind.execute(text("DROP AGGREGATE IF EXISTS array_accum(anyarray);"))
        bind.execute(
            text(
                """
                CREATE AGGREGATE array_accum (anyarray)
                (
                    sfunc = array_cat,
                    stype = anyarray,
                    initcond = '{}'
                );  
                """
            )
        )
    system_dictionary_additive_migration(bind)
    privacy_declaration_additive_migration(bind)


def downgrade():
    pass
