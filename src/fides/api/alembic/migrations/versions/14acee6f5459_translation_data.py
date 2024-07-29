"""migrate translation data - notices and experiences

Revision ID: 14acee6f5459
Revises: 0c65325843bd
Create Date: 2024-01-09 21:17:13.115020

"""

import csv
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy

from fides.api.alembic.migrations.helpers.database_functions import generate_record_id

# revision identifiers, used by Alembic.

revision = "14acee6f5459"
down_revision = "0c65325843bd"
branch_labels = None
depends_on = None


EXPERIENCE_CONFIG_DEFAULTS = [
    {
        "id": "pri-76b8-cc52-11ee-9eaa-8ef97a-modal-config",
        "name": "US Modal",
        "regions": ["us_ca", "us_co", "us_ct", "us_ut", "us_va"],
        "component": "modal",
        "allow_language_selection": False,
        "auto_detect_language": True,
        "dismissable": True,
        "disabled": True,
        "privacy_notice_keys": ["data_sales_and_sharing"],
        "origin": "pri-76b8-cc52-11ee-9eaa-8ef97a-modal",
    },
    {
        "id": "pri-27d4-cc53-11ee-9eaa-8ef97a04-pri-config",
        "name": "US Privacy Center",
        "regions": ["us_ca", "us_co", "us_ct", "us_ut", "us_va"],
        "component": "privacy_center",
        "allow_language_selection": False,
        "auto_detect_language": True,
        "dismissable": True,
        "disabled": True,
        "privacy_notice_keys": ["data_sales_and_sharing"],
        "origin": "pri-27d4-cc53-11ee-9eaa-8ef97a04-pri",
    },
    {
        "id": "pri-c8ff-78d6-4a02-850f-2c0ban-modal-config",
        "name": "EEA Banner + Modal",
        "regions": [
            "be",
            "bg",
            "cz",
            "dk",
            "de",
            "ee",
            "ie",
            "gr",
            "es",
            "fr",
            "hr",
            "it",
            "cy",
            "lv",
            "lt",
            "lu",
            "hu",
            "mt",
            "nl",
            "at",
            "pl",
            "pt",
            "ro",
            "si",
            "sk",
            "fi",
            "se",
            "gb",
            "is",
            "no",
            "li",
        ],
        "component": "banner_and_modal",
        "allow_language_selection": False,
        "auto_detect_language": True,
        "dismissable": True,
        "disabled": True,
        "privacy_notice_keys": ["essential", "functional", "analytics", "marketing"],
        "origin": "pri-c8ff-78d6-4a02-850f-2c0ban-modal",
    },
    {
        "id": "pri-694e-02bd-4afe-81b3-2a2ban-modal-config",
        "name": "Canada Banner + Modal",
        "regions": [
            "ca",
        ],
        "component": "banner_and_modal",
        "allow_language_selection": False,
        "auto_detect_language": True,
        "dismissable": True,
        "disabled": True,
        "privacy_notice_keys": ["marketing"],
        "origin": "pri-694e-02bd-4afe-81b3-2a2ban-modal",
    },
    {
        "id": "pri-d9ed6-25e7-4953-8977-772ban-modal-config",
        "name": "Quebec Banner + Modal",
        "regions": [
            "ca_qc",
        ],
        "component": "banner_and_modal",
        "allow_language_selection": False,
        "auto_detect_language": True,
        "dismissable": True,
        "disabled": True,
        "privacy_notice_keys": ["essential", "analytics", "marketing"],
        "origin": "pri-d9ed6-25e7-4953-8977-772ban-modal",
    },
    {
        "id": "d7c3ce0a-a3b3-43ff-bf6f-3d8-tcf-over-config",
        "name": "TCF",
        "allow_language_selection": False,
        "auto_detect_language": True,
        "dismissable": True,
        "disabled": True,
        "notices": [],
        "regions": [
            "be",
            "bg",
            "cz",
            "dk",
            "de",
            "ee",
            "ie",
            "gr",
            "es",
            "fr",
            "hr",
            "it",
            "cy",
            "lv",
            "lt",
            "lu",
            "hu",
            "mt",
            "nl",
            "at",
            "pl",
            "pt",
            "ro",
            "si",
            "sk",
            "fi",
            "se",
            "gb",
            "is",
            "no",
            "li",
            "eea",
        ],
        "component": "tcf_overlay",
        "privacy_notice_keys": [],
        "origin": "d7c3ce0a-a3b3-43ff-bf6f-3d8-tcf-over",
    },
]

# the known existing (legacy) experience config IDs.
# we will only attempt to migrate config data from these experience configs
KNOWN_EXISTING_EXPERIENCE_CONFIGS = {
    "pri-7ae3-f06b-4096-970f-0bbbdef-over",
    "pri-097a-d00d-40b6-a08f-f8e50def-pri",
    "a4974670-abad-471f-9084-2cb-tcf-over",
}


# this ties a DB record ID to our logical identifier of the type of OOB experience.
# the DB record ID is based on what we've defined in the associated config yml.
class DefaultExperienceConfigTypes(Enum):
    EEA_BANNER_AND_MODAL = "pri-c8ff-78d6-4a02-850f-2c0ban-modal-config"
    EEA_TCF_OVERLAY = "d7c3ce0a-a3b3-43ff-bf6f-3d8-tcf-over-config"
    US_MODAL = "pri-76b8-cc52-11ee-9eaa-8ef97a-modal-config"
    US_PRIVACY_CENTER = "pri-27d4-cc53-11ee-9eaa-8ef97a04-pri-config"
    CANADA_BANNER_MODAL = "pri-694e-02bd-4afe-81b3-2a2ban-modal-config"
    QUEBEC_BANNER_MODAL = "pri-d9ed6-25e7-4953-8977-772ban-modal-config"


class ComponentType(Enum):
    PrivacyCenter = "privacy_center"
    Overlay = "overlay"
    TCFOverlay = "tcf_overlay"


# our new OOB EEA (EU) experience configs, keyed by their component type
EEA_MAPPING = {
    ComponentType.Overlay: DefaultExperienceConfigTypes.EEA_BANNER_AND_MODAL,
    ComponentType.TCFOverlay: DefaultExperienceConfigTypes.EEA_TCF_OVERLAY,
}

# our new OOB US experience configs, keyed by their component type
US_MAPPING = {
    ComponentType.PrivacyCenter: DefaultExperienceConfigTypes.US_PRIVACY_CENTER,
    ComponentType.Overlay: DefaultExperienceConfigTypes.US_MODAL,
}

# our new OOB Canada experience configs, keyed by their component type
CANADA_MAPPING = {
    ComponentType.Overlay: DefaultExperienceConfigTypes.CANADA_BANNER_MODAL,
}

QUEBEC_MAPPING = {
    ComponentType.Overlay: DefaultExperienceConfigTypes.QUEBEC_BANNER_MODAL,
}

# this map contains the biggest _assumption_ about the migration -
# these are the notices that will be associated with our new OOB experience configs.
# any existing notices besides these will remain "orphaned" post-migration.
# additionally, the regions that (pre-migration) are associated with these notices
# will be used to infer the regions associated with the post-migration experience
# configs to which they map.
NOTICES_TO_EXPERIENCE_CONFIG = {
    "marketing": [EEA_MAPPING, CANADA_MAPPING, QUEBEC_MAPPING],
    "functional": [EEA_MAPPING],
    "essential": [EEA_MAPPING, QUEBEC_MAPPING],
    "analytics": [EEA_MAPPING, QUEBEC_MAPPING],
    "data_sales_and_sharing": [US_MAPPING],
}


# as part of this upgrade, we're removing the following GB sub-regions as region options across the app
GB_REGIONS_TO_REMOVE = {
    "gb_eng",
    "gb_sct",
    "gb_wls",
    "gb_nir",
}
# the GB sub-regions are replaced by the `gb` region
GB_REGIONS_TO_ADD = {
    "gb",
}

# Canadian regions are ignored in the migration of existing data, since we create a net-new OOB experience config for Canada
CA_REGIONS_TO_IGNORE = {
    "ca_qc",
    "ca_nt",
    "ca_nb",
    "ca_nu",
    "ca_bc",
    "ca_mb",
    "ca_ns",
    "ca_pe",
    "ca_sk",
    "ca_yt",
    "ca_on",
    "ca_nl",
    "ca_ab",
    "ca",
}


def dump_table_to_csv(bind, table_name):
    csv_file_path = f'./multilang_migration_backup_{table_name}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
    query = text(f"SELECT * FROM {table_name}")
    result = bind.execute(query)

    # Get column names from the result set
    column_names = result.keys()

    try:
        # Write results to CSV
        with open(csv_file_path, "w") as csv_file:
            csv_writer = csv.writer(csv_file)

            # Write header row
            csv_writer.writerow(column_names)

            # Write data rows
            for row in result:
                csv_writer.writerow(row)
    except PermissionError:
        logger.exception(
            f"Permission error writing migration backup file {csv_file_path}"
        )


def load_default_experience_configs():
    """
    Loads default experience config definitions from yml file.

    Returns two dicts in a tuple:
        - first dict holds "new" experience config records that will be used to reconcile existing data
        - second dict holds the "raw" experience config records based on the definitions on disk. these will be used as a reference for e.g. template creation.
    """
    _raw_experience_config_map = (
        {}
    )  # this will just hold config templates exactly as they are in the 'oob' file
    _reconciled_experience_config_map = (
        {}
    )  # will hold experience configs 'reconciled' between existing data and 'oob' template data

    for experience_config in EXPERIENCE_CONFIG_DEFAULTS:
        experience_config_type = DefaultExperienceConfigTypes(experience_config["id"])
        _raw_experience_config_map[experience_config_type] = experience_config.copy()

        # the reconciled experience config will have its regions populated by existing notices that are
        # associated with this experience config. so in most cases, we start "fresh" with an empty set.
        # the TCF experience and Canada/Quebec banner modal experiences are exceptions:
        # their regions are not derived from existing notices (TCF is not linked to notices; Canada experience config is net-new),
        # so we hardcode their regions to the config defaults.
        if experience_config_type not in (
            DefaultExperienceConfigTypes.EEA_TCF_OVERLAY,
            DefaultExperienceConfigTypes.CANADA_BANNER_MODAL,
            DefaultExperienceConfigTypes.QUEBEC_BANNER_MODAL,
        ):
            experience_config["regions"] = set()
        else:
            experience_config["regions"] = set(experience_config["regions"])

        experience_config["privacy_notices"] = set()
        experience_config["needs_migration"] = (
            False  # indicator whether the record requires migration, or we can default to the template values
        )
        _reconciled_experience_config_map[experience_config_type] = experience_config
        experience_config["needs_migration"] = False
    return _reconciled_experience_config_map, _raw_experience_config_map


(
    reconciled_experience_config_map,
    raw_experience_config_map,
) = load_default_experience_configs()


def backup_existing_data_csv(bind):
    """
    Perform a backup (dump to csv) of the data in our tables that will be impacted by migration.

    Because this data migration is risky, it is recommended to perform a comprehensive DB backup/snapshot beforehand!
    The "automated" dump to CSV here is an additional safety measure.
    """
    for table_name in [
        "privacyexperience",
        "privacyexperienceconfig",
        "privacyexperienceconfighistory",
        "privacynotice",
        "privacynoticehistory",
    ]:
        try:
            dump_table_to_csv(bind, table_name)
        except Exception:
            # permission error is handled within the function, but just to be extra safe
            # let's make sure our migration proceeds if ANY error is thrown from the CSV dump,
            # since this is just a nice-to-have.
            logger.exception(f"Error backing up table {table_name} to disk")


def remove_existing_experience_data(bind):
    """
    We remove any existing PrivacyExperience and PrivacyExperienceConfig records,
    to allow for a "clean-slate" in creation of _new_ PrivacyExperienceConfigs based on the
    "out of the box" templates.

    This means that any existing user-edited data on PrivacyExperienceConfig records will need to be
    _manually_ re-added to the post-migration state. It will not be migrated as part of the automatic migration.
    """

    def delete_experiences(bind):
        """
        Delete all PrivacyExperience records.

        These records will be effectively re-created as a result of the "out of the box" creation
        of 'new-style' PrivacyExperienceConfig records post-migration.
        """
        bind.execute(
            text(
                """
                DELETE FROM privacyexperience;
                """
            )
        )

    def delete_experience_configs(bind):
        """
        Delete all PrivacyExperienceConfig records.

        These records will be effectively re-created via the server's "out of the box" creation
        of the updated PrivacyExperienceConfig records, post-migration.
        """
        bind.execute(
            text(
                """
                DELETE FROM privacyexperienceconfig;
                """
            )
        )

    delete_experiences(bind)
    delete_experience_configs(bind)


def is_canada_or_quebec_experience(
    config_type: Optional[DefaultExperienceConfigTypes],
) -> bool:
    """Helper to determine whether the target experience config type is a canada or quebec experience"""
    return config_type in {
        DefaultExperienceConfigTypes.CANADA_BANNER_MODAL,
        DefaultExperienceConfigTypes.QUEBEC_BANNER_MODAL,
    }


def determine_needed_experience_configs(bind):
    """
    Our data model changes necessitate the creation of new Experience Configs. Now that "where" a Notice is served
    is being moved from the "Notice" constructs to "Experiences", existing Experience Configs are not sufficient
    to capture the full range of configuration on current Notices.
    """

    notice_query = """select id, name, regions, disabled, displayed_in_overlay, displayed_in_privacy_center, notice_key from privacynotice;"""
    experience_config_query = """SELECT id, component, disabled, accept_button_label, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title, banner_description, banner_title, reject_button_label, acknowledge_button_label from privacyexperienceconfig;"""

    existing_notices: ResultProxy = bind.execute(text(notice_query))
    for existing_notice in existing_notices:
        notice_key = existing_notice["notice_key"]
        component_mappings = NOTICES_TO_EXPERIENCE_CONFIG.get(notice_key, [])
        if component_mappings:
            for component_mapping in component_mappings:
                if is_canada_or_quebec_experience(
                    component_mapping.get(ComponentType.Overlay)
                ):
                    # If this is a Canadian/Quebec Banner and Modal, skip updating regions, and just use OOB
                    regions_to_add = set()
                else:
                    regions_to_add = set(existing_notice["regions"]).copy()

                    # remove GB subregions and replace with top-level `gb` region!
                    if not GB_REGIONS_TO_REMOVE.isdisjoint(
                        regions_to_add
                    ):  # if we have GB regions to remove
                        regions_to_add.difference_update(
                            GB_REGIONS_TO_REMOVE
                        )  # remove the GB regions
                        regions_to_add.update(GB_REGIONS_TO_ADD)  # add the GB region

                    # ignore any canada regions in migration - they are not migrated,
                    # but instead handled by a net-new OOB experience
                    regions_to_add.difference_update(CA_REGIONS_TO_IGNORE)

                if existing_notice["displayed_in_overlay"]:
                    experience_config = component_mapping.get(ComponentType.Overlay)
                    if experience_config:
                        reconciled_experience_config_map[experience_config][
                            "regions"
                        ].update(regions_to_add)
                        reconciled_experience_config_map[experience_config][
                            "privacy_notices"
                        ].add(existing_notice["id"])
                        if not existing_notice[
                            "disabled"
                        ] and not is_canada_or_quebec_experience(experience_config):
                            # Disabled by default, but if not a Canada/Quebec experience and any notices are enabled,
                            # let's enable this Experience Config as the safer default
                            reconciled_experience_config_map[experience_config][
                                "disabled"
                            ] = False
                        reconciled_experience_config_map[experience_config][
                            "needs_migration"
                        ] = True

                if existing_notice["displayed_in_privacy_center"]:
                    experience_config = component_mapping.get(
                        ComponentType.PrivacyCenter
                    )
                    if experience_config:
                        reconciled_experience_config_map[experience_config][
                            "regions"
                        ].update(regions_to_add)
                        reconciled_experience_config_map[experience_config][
                            "privacy_notices"
                        ].add(existing_notice["id"])
                        if not existing_notice[
                            "disabled"
                        ] and not is_canada_or_quebec_experience(experience_config):
                            # Disabled by default, but if not a Canada/Quebec experience and any notices are enabled,
                            # let's enable this Experience Config as the safer default
                            reconciled_experience_config_map[experience_config][
                                "disabled"
                            ] = False

                        reconciled_experience_config_map[experience_config][
                            "needs_migration"
                        ] = True

    existing_experience_configs: ResultProxy = bind.execute(
        text(experience_config_query)
    )
    has_existing_experience_configs = False
    for eec in existing_experience_configs:
        # only migrate experience config data if its a known config
        if eec["id"] in KNOWN_EXISTING_EXPERIENCE_CONFIGS:
            has_existing_experience_configs = True
            component = ComponentType(eec["component"])
            configs = []

            # because we've given experiences a location dimension in this migration,
            # an existing experience effectively maps to two "new" default experiences -
            # one that is surfaced in the US (and is associated with "US" notices), and
            # one that is surfaced in the EU (and is associated with the "EU" notices).
            # because of this, we'll copy over existing experience text/attributes to _both_
            # of these corresponding new experience configs.
            if eea_config_id := EEA_MAPPING.get(component):
                configs.append(reconciled_experience_config_map.get(eea_config_id))
            if us_config_id := US_MAPPING.get(component):
                configs.append(reconciled_experience_config_map.get(us_config_id))
            if canada_config_id := CANADA_MAPPING.get(component):
                configs.append(reconciled_experience_config_map.get(canada_config_id))
            if quebec_config_id := QUEBEC_MAPPING.get(component):
                configs.append(reconciled_experience_config_map.get(quebec_config_id))
            for config in configs:
                if config:
                    config["accept_button_label"] = eec["accept_button_label"]
                    config["acknowledge_button_label"] = eec["acknowledge_button_label"]
                    config["banner_description"] = eec["banner_description"]
                    config["banner_title"] = eec["banner_title"]
                    config["description"] = eec["description"]
                    config["privacy_policy_link_label"] = eec[
                        "privacy_policy_link_label"
                    ]
                    config["privacy_policy_url"] = eec["privacy_policy_url"]
                    config["privacy_preferences_link_label"] = eec[
                        "privacy_preferences_link_label"
                    ]
                    config["reject_button_label"] = eec["reject_button_label"]
                    config["save_button_label"] = eec["save_button_label"]
                    config["title"] = eec["title"]
                    config["needs_migration"] = True

                    if eec["component"] == "tcf_overlay":
                        # TCF doesn't have notices so enable the new TCF overlay if its existing overlay is enabled
                        config["disabled"] = eec["disabled"]

    if has_existing_experience_configs:
        return reconciled_experience_config_map

    # if no existing experience configs are found, don't return the map, because no experience config migration is needed.
    # instead, we'll rely on the OOB loading of experience configs on server startup.
    # basically, this is allows us to bypass the data migration if we're not actually migrating a db that's been in use!
    return {}


def migrate_experiences(bind):
    """
    Migrates data from any existing ExperienceConfig records to the new, translation-based data model, and reconciles
    the old ExperienceConfig records with new, OOB ExperienceConfig records.

    - First the necessary existing ExperienceConfig and PrivacyNotice data is retrieved and stored in memory
    - It is then, in memory, reconciled with our new OOB ExperienceConfig records, which are loaded from a YAML definition on disk
    - Then, we remove all existing Experience and ExperienceConfig records to start from a 'blank slate'
    - Then, based on the reconciled existing ExperienceConfig data, we create new ExperienceConfig and Experience records
    """

    def create_new_experience_config_templates(experience_configs):
        for experience_config in experience_configs:
            # for config template record:
            # - `id` is the `origin` field from the config template record loaded from disk
            create_experience_config_template_query = text(
                """
                INSERT INTO experienceconfigtemplate (id, component, name, disabled, allow_language_selection, dismissable, privacy_notice_keys, regions, auto_detect_language)
                VALUES (:id, :component, :name, :disabled, :allow_language_selection, :dismissable, :privacy_notice_keys, :regions, :auto_detect_language)
                """
            )

            bind.execute(
                create_experience_config_template_query,
                {
                    **experience_config,
                    "id": experience_config[
                        "origin"
                    ],  # origin of the config record is the template ID
                },
            )

    def create_new_experience_config(experience_config):
        """
        Creates a new experience config based on the provided definition. Also creates corresponding history record.

        """
        # for config record:
        # - `id` is the `id` grabbed from our config template record
        # - `origin` is the `origin` grabbed from the config template
        create_experience_config_query = text(
            """
            INSERT INTO privacyexperienceconfig (id, version, origin, component, name, disabled, is_default, allow_language_selection, dismissable, auto_detect_language, accept_button_label, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title, banner_description, banner_title, reject_button_label, acknowledge_button_label)
            VALUES (:id,  :version, :origin, :component, :name, :disabled, :is_default, :allow_language_selection, :dismissable, :auto_detect_language, :accept_button_label, :description, :privacy_preferences_link_label, :privacy_policy_link_label, :privacy_policy_url, :save_button_label, :title, :banner_description, :banner_title, :reject_button_label, :acknowledge_button_label)
            """
        )

        bind.execute(
            create_experience_config_query,
            {
                **experience_config,
                "version": 1,
                "is_default": True,
            },
        )

        # for history record:
        # - `id` is a generated UUID
        # - `experience_config_id` is the `id` grabbed from our config template record on disk
        # - `origin` is the `origin` grabbed from the config template record on disk
        create_experience_config_history = text(
            """
             INSERT INTO privacyexperienceconfighistory (id, experience_config_id, origin, name, disabled, version, component, is_default, allow_language_selection, auto_detect_language, dismissable, accept_button_label, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title, banner_description, banner_title, reject_button_label, acknowledge_button_label, language)
             VALUES (:history_id, :id, :origin, :name, :disabled, :version, :component, :is_default, :allow_language_selection, :auto_detect_language, :dismissable, :accept_button_label, :description, :privacy_preferences_link_label, :privacy_policy_link_label, :privacy_policy_url, :save_button_label, :title, :banner_description, :banner_title, :reject_button_label, :acknowledge_button_label, :language)
            """
        )

        bind.execute(
            create_experience_config_history,
            {
                **experience_config,
                "history_id": generate_record_id("pri"),
                "version": 1,
                "is_default": True,
                "language": "en",
            },
        )

    def create_applicable_experiences(experience_config):
        """
        Creates all the applicable experience records based on the provided experience config definition.

        i.e., looks at all regions on the provided experience config definition, and creates a corresponding
        experience record for each region.
        """
        new_experience = text(
            """
            INSERT INTO privacyexperience (id, experience_config_id, region)
            VALUES(:experience_id, :experience_config_id, :region)
            """
        )
        for region in experience_config["regions"]:
            if region is not None:
                bind.execute(
                    new_experience,
                    {
                        "experience_id": generate_record_id("pri"),
                        "experience_config_id": experience_config["id"],
                        "region": region,
                    },
                )

    def link_notices_to_experiences(experience_config):
        """
        Creates experience notice records based on the provided experience config definition.

        i.e., looks at all `privacy_notices` linked to the experience config, and creates a corresponding
        experience notice record for each linked notice.
        """
        link_notice_query = text(
            """
                INSERT INTO experiencenotices (id, notice_id, experience_config_id)
                VALUES (:record_id, :notice_id, :experience_config_id)
                """
        )
        for notice_id in experience_config["privacy_notices"]:
            bind.execute(
                link_notice_query,
                {
                    "record_id": generate_record_id("exp"),
                    "notice_id": notice_id,
                    "experience_config_id": experience_config["id"],
                },
            )

    def create_experience_translations(bind):
        """
        Creates new experience translation records for each privacy experience config record in the db.

        We simply take the text that's been temporarily saved on the config record directly and move it
        over to the translation record. The translation is assumed to be english.

        This requires the privacy experience config records to have been created before this is invoked!

        """
        get_experience_config_ids = text(
            """SELECT id FROM privacyexperienceconfig;
         """
        )

        # for translation record:
        # - `id` is a generated UUID
        # - `experience_config_id` is the `id` column grabbed from the experience config query result
        # - language is assumed to be english!
        create_translation_query = text(
            """
            INSERT INTO experiencetranslation (id, experience_config_id, created_at, updated_at, language, is_default, accept_button_label, reject_button_label, acknowledge_button_label, banner_description, banner_title, description, title,  privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label)
            SELECT :record_id, id, created_at, updated_at, :language, :is_default, accept_button_label, reject_button_label, acknowledge_button_label, banner_description, banner_title, description, title,  privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label
            FROM privacyexperienceconfig
            WHERE id = :experience_config_id
            """
        )
        for res in bind.execute(get_experience_config_ids):
            # Create a translation for each Experience
            bind.execute(
                create_translation_query,
                {
                    "record_id": generate_record_id("exp"),
                    "language": "en",
                    "experience_config_id": res["id"],
                    "is_default": True,
                },
            )

        # Repoint the Experience Config History to the Experience Translation
        link_config_to_translation_id = text(
            """
            UPDATE privacyexperienceconfighistory
            SET translation_id = experiencetranslation.id
            FROM experiencetranslation
            WHERE experiencetranslation.experience_config_id = privacyexperienceconfighistory.experience_config_id;
        """
        )

        bind.execute(link_config_to_translation_id)

    # first extract existing experience (config) data needed for migration
    experience_configs = determine_needed_experience_configs(bind)

    # before wiping data, let's perform a csv backup to disk just to be extra safe
    backup_existing_data_csv(bind)

    # wipe the existing experience + experience config data to start from a blank slate
    remove_existing_experience_data(bind)

    # if we don't have experience configs, we can bypass all experience config data migration
    if experience_configs:
        # first create experience config templates based on raw experience config definitions
        create_new_experience_config_templates(raw_experience_config_map.values())

        # create new experience + experience configs based on old experience config data
        # these have been reconciled with the new OOB experience config records
        for experience_config_type in DefaultExperienceConfigTypes:
            logger.info(f"Migrating experience config {experience_config_type.name}")
            reconciled_experience_config = experience_configs.get(
                experience_config_type, {}
            )
            raw_experience_config = raw_experience_config_map.get(
                experience_config_type, {}
            )

            if not reconciled_experience_config and not raw_experience_config:
                logger.info(
                    f"No reconciled or raw experience config found for {experience_config_type.name}"
                )
                continue

            # revert to the "raw" config if we haven't flagged a config as needing migration
            # in practice, we should always have a reconciled record here that's flagged for migration,
            # but this covers our bases in case anyone has e.g. deleted a previous OOB notice.
            if reconciled_experience_config.get("needs_migration", False):
                logger.info(
                    f"Migrating reconciled experience config {reconciled_experience_config['id']}"
                )
                experience_config_type = reconciled_experience_config
            else:
                logger.info(
                    f"Creating raw experience config {raw_experience_config['id']}"
                )
                experience_config_type = raw_experience_config

            create_new_experience_config(experience_config_type)
            create_applicable_experiences(experience_config_type)
            link_notices_to_experiences(experience_config_type)

        # experience translations are then created based on the new experience config records
        create_experience_translations(bind)


def migrate_notices(bind):
    """
    Migrates existing PrivacyNotice records to the new, translation-based data model.

    Notice keys are not impacted. Most existing notice data is moved onto a linked NoticeTranslation record,
    which is assumed to be english-language as a default. If the existing notice text/content is _not_ english-language,
    then users will need to *manually* adjust the language on the created translation record.

    The existing PrivacyNoticeHistory records are adjusted to point to the associated NoticeTranslation record,
    as is expected in the new data model.
    """

    get_notices_query = text(
        """SELECT id from privacynotice;
         """
    )

    create_notice_translation_query = text(
        """
        INSERT INTO noticetranslation (id, privacy_notice_id, language, title, description, created_at, updated_at)
        SELECT :record_id, :original_notice_id, :language, name, description, created_at, updated_at
        FROM privacynotice
        WHERE id = :original_notice_id
        """
    )
    for res in bind.execute(get_notices_query):
        # Create a Notice Translation for each notice, setting to english as a default
        bind.execute(
            create_notice_translation_query,
            {
                "record_id": generate_record_id("pri"),
                "language": "en",
                "original_notice_id": res["id"],
            },
        )

    # Add a FK from the Notice History back to the Notice Translation
    link_notice_history_to_translation_id = text(
        """
        UPDATE privacynoticehistory
        SET translation_id = noticetranslation.id, title = privacynoticehistory.name
        FROM noticetranslation
        WHERE noticetranslation.privacy_notice_id = privacynoticehistory.privacy_notice_id;
        """
    )

    bind.execute(link_notice_history_to_translation_id)

    # Queries the latest historical version for each notice
    new_notice_histories_to_create_query = text(
        """
        select privacy_notice_id, max(version) from privacynoticehistory group by privacy_notice_id;
        """
    )
    # Create a new privacy notice history record that bumps the version and clears regions and displayed_in* fields and sets language
    for res in bind.execute(new_notice_histories_to_create_query):
        create_privacy_notice_history_query = text(
            """
            INSERT INTO privacynoticehistory (id, name, description, origin, consent_mechanism, data_uses, version, disabled, enforcement_level, has_gpc_flag, internal_description, notice_key, gpp_field_mapping, framework, language, title, translation_id, privacy_notice_id)
            SELECT :record_id, name, description, origin, consent_mechanism, data_uses, :new_version, disabled, enforcement_level, has_gpc_flag, internal_description, notice_key, gpp_field_mapping, framework, :language, title, translation_id, privacy_notice_id
            FROM privacynoticehistory
            WHERE version = :current_version AND
            privacy_notice_id = :privacy_notice_id
            ORDER BY created_at DESC LIMIT 1
        """
        )
        bind.execute(
            create_privacy_notice_history_query,
            {
                "record_id": generate_record_id("pri"),
                "language": "en",
                "new_version": res["max"] + 1,
                "current_version": res["max"],
                "privacy_notice_id": res["privacy_notice_id"],
            },
        )


def downward_migrate_notices(bind):
    """
    Back-migration of PrivacyNotice data.

    Moves data in existing NoticeTranslation records back to the associated PrivacyNotice records,
    to match the old data model.
    # NOTE: this won't work _well_ if multiple translations are present. Should we even attempt it?

    The existing PrivacyNoticeHistory records are adjusted to point back to the associated PrivacyNotice records,
    rather than the NoticeTranslation records, as is expected in the old data model.

    """
    noticetranslation_data_to_notice_query = text(
        """
        UPDATE privacynotice
        SET name = noticetranslation.title, description = noticetranslation.description
        FROM noticetranslation
        WHERE noticetranslation.privacy_notice_id = privacynotice.id
        """
    )
    bind.execute(noticetranslation_data_to_notice_query)

    # Update the FK from the Notice History back to the Notice record
    link_notice_history_to_notice = text(
        """
        UPDATE privacynoticehistory
        SET privacy_notice_id = noticetranslation.privacy_notice_id
        FROM noticetranslation
        WHERE noticetranslation.id = privacynoticehistory.translation_id;
    """
    )

    bind.execute(link_notice_history_to_notice)


def upgrade():
    logger.info(
        f"Starting Consent Multitranslation Data Migration (#2) {datetime.now()}"
    )

    bind = op.get_bind()

    migrate_experiences(bind)

    migrate_notices(bind)


def downgrade():
    # Downgrade will _not_ attempt to recreate PrivacyExperienceConfig recrords,
    # as that should be handled by the (old) server's OOB loading behavior
    bind = op.get_bind()

    downward_migrate_notices(bind)

    bind.execute(
        text(
            """
            DELETE FROM experiencetranslation;
            """
        )
    )
    remove_existing_experience_data(
        bind
    )  # remove existing experience data to ensure it won't prevent startup on downgraded versions!
