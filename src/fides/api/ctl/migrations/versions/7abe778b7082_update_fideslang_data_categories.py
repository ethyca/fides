from __future__ import annotations

"""Update fideslang data categories

Revision ID: 7abe778b7082
Revises: bab75915670a
Create Date: 2022-07-29 17:54:53.719453

"""
import logging

from sqlalchemy.exc import ProgrammingError

from fides.api.ops.db.base import DatasetConfig
from fides.core.config import get_config
from fides.lib.db.session import get_db_session

CONFIG = get_config()

logger = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision = "7abe778b7082"
down_revision = "bab75915670a"
branch_labels = None
depends_on = None


DATA_MAP_UPGRADE = {
    "account.payment": "user.financial.payment_information",
    "user.derived.identifiable.biometric_health": "user.biometric_health",
    "user.derived.identifiable.browsing_history": "user.browsing_history",
    "user.derived.identifiable.demographic": "user.demographic",
    "user.derived.identifiable.device": "user.device",
    "user.derived.identifiable.device.cookie_id": "user.device.cookie_id",
    "user.derived.identifiable.device.device_id": "user.device.device_id",
    "user.derived.identifiable.device.ip_address": "user.device.ip_address",
    "user.derived.identifiable.gender": "user.gender",
    "user.derived.identifiable.location": "user.location",
    "user.derived.identifiable.media_consumption": "user.media_consumption",
    "user.derived.identifiable.non_specific_age": "user.non_specific_age",
    "user.derived.identifiable.observed": "user.observed",
    "user.derived.identifiable.profiling": "user.profiling",
    "user.derived.identifiable.race": "user.race",
    "user.derived.identifiable.religious_belief": "user.religious_belief",
    "user.derived.identifiable.search_history": "user.search_history",
    "user.derived.identifiable.sexual_orientation": "user.sexual_orientation",
    "user.derived.identifiable.social": "user.social",
    "user.derived.identifiable.telemetry": "user.telemetry",
    "user.derived.identifiable.unique_id": "user.unique_id",
    "user.derived.identifiable.user_sensor": "user.sensor_data",
    "user.derived.identifiable.organization": "user.organization",
    "user.derived.identifiable.workplace": "user.workplace",
    "user.provided.identifiable.biometric": "user.biometric",
    "user.provided.identifiable.childrens": "user.childrens",
    "user.provided.identifiable.contact.city": "user.contact.address.city",
    "user.provided.identifiable.contact.country": "user.contact.address.country",
    "user.provided.identifiable.contact.postal_code": "user.contact.address.postal_code",
    "user.provided.identifiable.contact.state": "user.contact.address.state",
    "user.provided.identifiable.contact.street": "user.contact.address.street",
    "user.provided.identifiable.contact.email": "user.contact.email",
    "user.provided.identifiable.contact.phone_number": "user.contact.phone_number",
    "user.provided.identifiable.credentials": "user.credentials",
    "user.provided.identifiable.credentials.biometric_credentials": "user.credentials.biometric_credentials",
    "user.provided.identifiable.credentials.password": "user.credentials.password",
    "user.provided.identifiable.date_of_birth": "user.date_of_birth",
    "user.provided.identifiable.financial": "user.financial",
    "user.provided.identifiable.financial.account_number": "user.financial.account_number",
    "user.provided.identifiable.gender": "user.gender",
    "user.provided.identifiable.genetic": "user.genetic",
    "user.provided.identifiable.government_id": "user.government_id",
    "user.provided.identifiable.government_id.drivers_license_number": "user.government_id.drivers_license_number",
    "user.provided.identifiable.government_id.national_identification_number": "user.government_id.national_identification_number",
    "user.provided.identifiable.government_id.passport_number": "user.government_id.passport_number",
    "user.provided.identifiable.health_and_medical": "user.health_and_medical",
    "user.provided.identifiable.job_title": "user.job_title",
    "user.provided.identifiable.name": "user.name",
    "user.provided.identifiable.non_specific_age": "user.non_specific_age",
    "user.provided.identifiable.political_opinion": "user.political_opinion",
    "user.provided.identifiable.race": "user.race",
    "user.provided.identifiable.religious_belief": "user.religious_belief",
    "user.provided.identifiable.sexual_orientation": "user.sexual_orientation",
    "user.provided.identifiable.workplace": "user.provided.identifiable.workplace",
}

DATA_MAP_DOWNGRADE = {v: k for k, v in DATA_MAP_UPGRADE.items()}


def is_removed_downgrade(privacy_key: str) -> bool:
    removed = (
        "user.contact.address",
        "user.contact.address.number",
        "user.financial.payment_information",
        "user.name.first",
        "user.name.last",
    )

    return privacy_key in removed


def is_removed_upgrade(privacy_key: str) -> bool:
    removed = (
        "account",
        "account.contact",
        "account.contact.city",
        "account.contact.country",
        "account.contact.email",
        "account.contact.phone_number",
        "account.contact.postal_code",
        "account.contact.state",
        "account.contact.street",
        "account.payment.financial_account_number",
        "user.derived",
        "user.derived.identifiable",
        "user.derived.nonidentifiable",
        "user.derived.nonidentifiable.sensor",
        "user.provided",
        "user.provided.identifiable",
        "user.provided.nonidentifiable",
    )

    return privacy_key in removed


def update_field(field: dict, migration_direction: str) -> dict:
    data_categories = field.get("data_categories", [])
    updated = []
    if migration_direction == "up":
        for data_category in data_categories:
            if is_removed_upgrade(data_category):
                logger.info(
                    "Removing %s, this is no longer a valid category", data_category
                )
            if data_category:
                if not is_removed_upgrade(data_category):
                    new = DATA_MAP_UPGRADE.get(data_category)
                    if new:
                        updated.append(new)
                    else:
                        updated.append(data_category)
                else:
                    updated.append(data_category)
        field["data_categories"] = updated
    else:
        for data_category in data_categories:
            if is_removed_downgrade(data_category):
                logger.info(
                    "Removing %s, this is no longer a valid category", data_category
                )
            if data_category:
                if not is_removed_downgrade(data_category):
                    new = DATA_MAP_DOWNGRADE.get(data_category)
                    if new:
                        updated.append(new)
                    else:
                        updated.append(data_category)
                else:
                    updated.append(data_category)
        field["data_categories"] = updated

    # Document databases like mongo can have nested fields so this is the reason
    # for the recursion here.
    if field.get("fields"):
        for field in field["fields"]:
            update_field(field, migration_direction)

    return field


def run_migration(migration_direction: str) -> None:
    sessionlocal = get_db_session(CONFIG)
    with sessionlocal() as session:
        try:
            datasets = DatasetConfig.all(db=session)

            logger.info("Upgrading fideslang categories")
            counter = 0
            for dataset in datasets:
                counter += 1
                if counter % 10 == 0:
                    logger.info("Upgrading fideslang categories")

                dataset_json = dataset.dataset
                collections = dataset_json.get("collections")

                if collections:
                    for collection in collections:
                        fields = collection.get("fields")
                        if fields:
                            for field in fields:
                                field = update_field(field, migration_direction)

        # If the datasetconfig table doesn't exist a ProgrammingError will be thrown.
        # If that happens we know there are no records to update so we can ignore the
        # error.
        except ProgrammingError:
            pass


def upgrade() -> None:
    run_migration("up")


def downgrade() -> None:
    run_migration("down")
