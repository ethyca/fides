"""translation data

Revision ID: 14acee6f5459
Revises: a1e23b70f2b2
Create Date: 2024-01-09 21:17:13.115020

"""

import uuid
from enum import Enum

import yaml
from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy

# revision identifiers, used by Alembic.

revision = "14acee6f5459"
down_revision = "a1e23b70f2b2"
branch_labels = None
depends_on = None


def generate_record_id(prefix):
    return prefix + "_" + str(uuid.uuid4())


class DefaultExperienceConfigTypes(Enum):
    EEA_PRIVACY_CENTER = 1
    EEA_MODAL_AND_BANNER = "pri-c8ff-78d6-4a02-850f-2c09dda-over-config"
    EEA_TCF_OVERLAY = "d7c3ce0a-a3b3-43ff-bf6f-3d8-tcf-over-config"
    US_MODAL = "pri-76b8-cc52-11ee-9eaa-8ef97a0-over-config"
    US_PRIVACY_CENTER = "pri-27d4-cc53-11ee-9eaa-8ef97a04-pri-config"


class ComponentType(Enum):
    PrivacyCenter = "privacy_center"
    Overlay = "overlay"
    TCFOverlay = "tcf_overlay"


EEA_MAPPING = {
    ComponentType.PrivacyCenter: DefaultExperienceConfigTypes.EEA_PRIVACY_CENTER,
    ComponentType.Overlay: DefaultExperienceConfigTypes.EEA_MODAL_AND_BANNER,
    ComponentType.TCFOverlay: DefaultExperienceConfigTypes.EEA_TCF_OVERLAY,
}
US_MAPPING = {
    ComponentType.PrivacyCenter: DefaultExperienceConfigTypes.US_PRIVACY_CENTER,
    ComponentType.Overlay: DefaultExperienceConfigTypes.US_MODAL,
}

NOTICES_TO_EXPERIENCE_CONFIG = {
    "marketing": EEA_MAPPING,
    "functional": EEA_MAPPING,
    "essential": EEA_MAPPING,
    "analytics": EEA_MAPPING,
    "data_sales_and_sharing": US_MAPPING,
}


def load_experience_config_from_files(file_paths):
    """
    Attempts loading the experience config from a set of given file paths until it finds a valid yaml
    """
    for path in file_paths:
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f).get("privacy_experience_configs")
        except FileNotFoundError:
            # If the file is not found in the current path, try the next one
            continue

    return None


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

    # this is a bit of a hack! but the path to the file depends on whether we're executing the migration
    # as part of app startup or as part of a 'manual' migration attempt
    experience_configs = load_experience_config_from_files(
        [
            "privacy_experience_config_defaults.yml",
            "src/fides/api/alembic/privacy_experience_config_defaults.yml",
        ]
    )

    for experience_config in experience_configs:
        _raw_experience_config_map[
            DefaultExperienceConfigTypes(experience_config["id"])
        ] = experience_config.copy()
        experience_config["regions"] = (
            set()
        )  # remove the configs regions, since we will populate based on existing notices
        experience_config["privacy_notices"] = set()  # initialize the notices field
        experience_config["needs_migration"] = (
            False  # indicator whether the record requires migration, or we can default to the template values
        )
        _reconciled_experience_config_map[
            DefaultExperienceConfigTypes(experience_config["id"])
        ] = experience_config
        experience_config["needs_migration"] = False
    return _reconciled_experience_config_map, _raw_experience_config_map


reconciled_experience_config_map, raw_experience_config_map = (
    load_default_experience_configs()
)


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


def determine_needed_experience_configs(bind):
    """
    Our data model changes necessitate the creation of new Experience Configs. Now that "where" a Notice is served
    is being moved from the "Notice" constructs to "Experiences", existing Experience Configs are not sufficient
    to capture the full range of configuration on current Notices.
    """

    notice_query = """select id, name, regions, displayed_in_overlay, displayed_in_privacy_center, notice_key from privacynotice;"""
    experience_config_query = """SELECT id, component, disabled, accept_button_label, banner_enabled, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title, banner_description, banner_title, reject_button_label, acknowledge_button_label from privacyexperienceconfig;"""

    existing_notices: ResultProxy = bind.execute(text(notice_query))
    for existing_notice in existing_notices:
        notice_key = existing_notice["notice_key"]
        component_mapping = NOTICES_TO_EXPERIENCE_CONFIG.get(notice_key)
        if component_mapping:
            if existing_notice["displayed_in_overlay"]:
                experience_config = component_mapping.get(ComponentType.Overlay)
                reconciled_experience_config_map[experience_config.name][
                    "regions"
                ].update(existing_notice["regions"])
                reconciled_experience_config_map[experience_config.name][
                    "privacy_notices"
                ].add(existing_notice["id"])
                reconciled_experience_config_map[experience_config.name][
                    "needs_migration"
                ] = True

            if existing_notice["displayed_in_privacy_center"]:
                experience_config = component_mapping.get(ComponentType.PrivacyCenter)
                reconciled_experience_config_map[experience_config.name][
                    "regions"
                ].update(existing_notice["regions"])
                reconciled_experience_config_map[experience_config.name][
                    "privacy_notices"
                ].add(existing_notice["id"])
                reconciled_experience_config_map[experience_config.name][
                    "needs_migration"
                ] = True

    existing_experience_configs: ResultProxy = bind.execute(
        text(experience_config_query)
    )
    has_existing_experience_configs = False
    for eec in existing_experience_configs:
        has_existing_experience_configs = True
        component = ComponentType(eec["component"])
        configs = []
        if eea_config_id := EEA_MAPPING.get(component):
            configs.append(reconciled_experience_config_map.get(eea_config_id.name))
        if us_config_id := US_MAPPING.get(component):
            configs.append(reconciled_experience_config_map.get(us_config_id.name))
        for config in configs:
            if config:
                config["accept_button_label"] = eec["accept_button_label"]
                config["acknowledge_button_label"] = eec["acknowledge_button_label"]
                config["banner_description"] = eec["banner_description"]
                config["banner_enabled"] = eec["banner_enabled"]
                config["banner_title"] = eec["banner_title"]
                config["description"] = eec["description"]
                config["privacy_policy_link_label"] = eec["privacy_policy_link_label"]
                config["privacy_policy_url"] = eec["privacy_policy_url"]
                config["privacy_preferences_link_label"] = eec[
                    "privacy_preferences_link_label"
                ]
                config["reject_button_label"] = eec["reject_button_label"]
                config["save_button_label"] = eec["save_button_label"]
                config["title"] = eec["title"]
                config["needs_migration"] = True

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
            create_experience_config_query = text(
                """
                INSERT INTO experienceconfigtemplate (id, component, name, disabled, privacy_notice_keys, regions)
                VALUES (:id, :component, :name, :disabled, :privacy_notice_keys, :regions)
                """
            )

            bind.execute(
                create_experience_config_query,
                {
                    "id": experience_config[
                        "origin"
                    ],  # origin of the config record is the template ID
                    "component": experience_config["component"],
                    "name": experience_config["name"],
                    "disabled": experience_config["disabled"],
                    "privacy_notice_keys": experience_config["privacy_notice_keys"],
                    "regions": experience_config["regions"],
                },
            )

    def create_new_experience_config(experience_config):
        """
        Creates a new experience config based on the provided definition. Also creates corresponding history record.
        """

        create_experience_config_query = text(
            """
            INSERT INTO privacyexperienceconfig (id, version, origin, component, name, disabled, is_default, accept_button_label, banner_enabled, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title, banner_description, banner_title, reject_button_label, acknowledge_button_label)
            VALUES (:id,  :version, :origin,  :component, :name, :disabled, :is_default, :accept_button_label, :banner_enabled, :description, :privacy_preferences_link_label, :privacy_policy_link_label, :privacy_policy_url, :save_button_label, :title, :banner_description, :banner_title, :reject_button_label, :acknowledge_button_label)
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

        create_experience_config_history = text(
            """
             INSERT INTO privacyexperienceconfighistory (id, experience_config_id, origin, name, disabled, version, component, is_default, accept_button_label, banner_enabled, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title, banner_description, banner_title, reject_button_label, acknowledge_button_label)
             VALUES (:history_id, :id, :origin, :name, :disabled, :version, :component, :is_default, :accept_button_label, :banner_enabled, :description, :privacy_preferences_link_label, :privacy_policy_link_label, :privacy_policy_url, :save_button_label, :title, :banner_description, :banner_title, :reject_button_label, :acknowledge_button_label)
            """
        )

        bind.execute(
            create_experience_config_history,
            {
                "history_id": generate_record_id("pri"),
                "version": 1,
                **experience_config,
                "is_default": True,
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
                    "language": "en_us",
                    "is_default": True,
                    "experience_config_id": res["id"],
                },
            )

        # Repoint the Experience Config History to the Experience Translation, and set dismissable while we're here.
        link_config_to_translation_id = text(
            """
            UPDATE privacyexperienceconfighistory
            SET translation_id = experiencetranslation.id, dismissable = dismissable
            FROM experiencetranslation
            WHERE experiencetranslation.experience_config_id = privacyexperienceconfighistory.experience_config_id;
        """
        )

        bind.execute(link_config_to_translation_id)

    # first extract existing experience (config) data needed for migration
    experience_configs = determine_needed_experience_configs(bind)

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
        SET translation_id = noticetranslation.id, title = privacynoticehistory.name, language = 'en'
        FROM noticetranslation
        WHERE noticetranslation.privacy_notice_id = privacynoticehistory.privacy_notice_id;
        """
    )

    bind.execute(link_notice_history_to_translation_id)


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
        SET name = noticetranslation.title, description = noticetranslation.description,
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
    bind = op.get_bind()

    migrate_experiences(bind)

    migrate_notices(bind)


def downgrade():
    # Downgrade will _not_ attempt to recreate PrivacyExperienceConfig recrords,
    # as that should be handled by the (old) server's OOB loading behavior
    bind = op.get_bind()

    downward_migrate_notices(bind)
    remove_existing_experience_data(
        bind
    )  # remove existing experience data to ensure it won't prevent startup on downgraded versions!
