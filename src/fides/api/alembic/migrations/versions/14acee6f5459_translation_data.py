"""translation data

Revision ID: 14acee6f5459
Revises: 4ee4876f4be1
Create Date: 2024-01-09 21:17:13.115020

"""
import uuid

from alembic import op
import pandas as pd
from sqlalchemy import text

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_colwidth", None)


# revision identifiers, used by Alembic.
from pandas import DataFrame

revision = "14acee6f5459"
down_revision = "4ee4876f4be1"
branch_labels = None
depends_on = None


def generate_record_id(prefix):
    return prefix + "_" + str(uuid.uuid4())


def determine_needed_experience_configs(bind):
    """
    Our data model changes necessitate the creation of new Experience Configs. Now that "where" a Notice is served
    is being moved from the "Notice" constructs to "Experiences", existing Experience Configs are not sufficient
    to capture the full range of configuration on current Notices.
    """

    notice_query = """select id, name, regions, displayed_in_overlay, displayed_in_privacy_center from privacynotice;"""
    experience_query = (
        """select experience_config_id, region, component from privacyexperience;"""
    )
    df: DataFrame = pd.read_sql(notice_query, bind)

    exp_df: DataFrame = pd.read_sql(experience_query, bind)

    def transform_components(row):
        components = []
        if row["displayed_in_overlay"]:
            components.append("overlay")

        if row["displayed_in_privacy_center"]:
            components.append("privacy_center")

        return components

    # Convert displayed_in_* fields to a list of components for consistency
    if not df.empty:
        df["component"] = df.apply(transform_components, axis=1)
    else:
        df["component"] = pd.Series(dtype=str)

    df = df.drop(["displayed_in_overlay", "displayed_in_privacy_center"], axis=1)

    # Expand to Notice x Region x Component
    df_component_expanded = df.explode("component")

    df_region_expanded = (
        df_component_expanded.explode("regions")
        .drop_duplicates()
        .reset_index(drop=True)
    )
    df_region_expanded = df_region_expanded.rename(columns={"regions": "region"})

    # Join Notice data with Experience data so we have Notice x Region x Component x Experience Config ID
    merged = pd.merge(exp_df, df_region_expanded, on=["region", "component"])

    def aggregate_list_fields(list_field):
        """Aggregate notices as a comma-separated string because we still need to do another group by
        and we can't do that on a list"""
        sorted_list = sorted(list(set(list_field)))
        return ",".join(sorted_list)

    # Collapse to |Notice| x Region x Component x Config
    grouped_df = (
        merged.groupby(["component", "region", "experience_config_id"])["id"]
        .agg(aggregate_list_fields)
        .reset_index()
    )

    # Collapse to |Notice| x |Region| x Component x Config
    next_group = (
        grouped_df.groupby(["id", "component", "experience_config_id"])["region"]
        .agg(aggregate_list_fields)
        .reset_index()
    )

    def convert_csstring_to_list_field(string_field):
        return string_field.str.split(",")

    next_group[["id", "region"]] = next_group[["id", "region"]].apply(
        lambda x: convert_csstring_to_list_field(x)
    )
    next_group["new_experience_config_needed"] = False

    next_group.loc[
        next_group.experience_config_id.duplicated(), "new_experience_config_needed"
    ] = True

    def get_experience_config_id_after(row):
        if not row["new_experience_config_needed"]:
            return row["experience_config_id"]

        if (
            set(row["region"]) == {"us_ca", "us_co", "us_ct", "us_ia", "us_ut", "us_va"}
            and row["component"] == "overlay"
            and row["experience_config_id"] == "pri-7ae3-f06b-4096-970f-0bbbdef-over"
        ):
            return "pri-4b6e-1165-4e12-8125-18f2db8-over"

        return generate_record_id("pri")

    if not next_group.empty:
        next_group["experience_config_id_after"] = next_group.apply(
            get_experience_config_id_after, axis=1
        )
    else:
        next_group["experience_config_id_after"] = pd.Series(dtype=str)
    return next_group


def upgrade():
    bind = op.get_bind()

    experience_config_df: DataFrame = determine_needed_experience_configs(bind)

    def create_new_experience_config(row):
        clone_experience_config_query = text(
            """
            INSERT INTO privacyexperienceconfig (id, version, component, disabled, is_default, accept_button_label, banner_enabled, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title, banner_description, banner_title, reject_button_label, acknowledge_button_label)
            SELECT :id, :version, component, disabled, is_default, accept_button_label, banner_enabled, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title, banner_description, banner_title, reject_button_label, acknowledge_button_label
            FROM privacyexperienceconfig
            WHERE privacyexperienceconfig.id = :original_id
            """
        )

        bind.execute(
            clone_experience_config_query,
            {
                "id": row["experience_config_id_after"],
                "original_id": row["experience_config_id"],
                "version": 1,
            },
        )

        create_experience_config_history = text(
            """
             INSERT INTO privacyexperienceconfighistory (id, experience_config_id, disabled, version, component, is_default, accept_button_label, banner_enabled, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title)
             SELECT :id, :experience_config_id, disabled, :version, component, is_default, accept_button_label, banner_enabled, description, privacy_preferences_link_label, privacy_policy_link_label, privacy_policy_url, save_button_label, title
             FROM privacyexperienceconfig
             WHERE privacyexperienceconfig.id = :original_id
            """
        )

        bind.execute(
            create_experience_config_history,
            {
                "id": generate_record_id("pri"),
                "experience_config_id": row["experience_config_id_after"],
                "original_id": row["experience_config_id"],
                "version": 1,
            },
        )

    # Create any needed Experience Configs that don't have coverage when we move notices and displayed_in_*
    experience_config_df[experience_config_df["new_experience_config_needed"]].apply(
        create_new_experience_config, axis=1
    )

    def link_new_config_to_applicable_experiences(row):
        point_experience_to_new_config = text(
            """
            UPDATE privacyexperience
            SET experience_config_id = :new_config_id
            WHERE component = :component and region in :regions
            """
        )
        bind.execute(
            point_experience_to_new_config,
            {
                "component": row["component"],
                "new_config_id": row["experience_config_id_after"],
                "regions": tuple(row["region"]),
            },
        )

    # Add a FK linking applicable Experiences to Experience Configs.
    # This is the equivalent of setting "locations" on Experience Configs
    experience_config_df[experience_config_df["new_experience_config_needed"]].apply(
        link_new_config_to_applicable_experiences, axis=1
    )

    # Translate "disabled" concept from the Experience Config -> Privacy Experience.
    set_experience_disabled = text(
        """
        UPDATE privacyexperience
        SET disabled = privacyexperienceconfig.disabled
        FROM privacyexperienceconfig
        WHERE privacyexperience.experience_config_id = privacyexperienceconfig.id;
        """
    )

    bind.execute(set_experience_disabled)

    def link_notices_to_experiences(row):
        link_notice_query = text(
            """
            INSERT INTO experiencenotices (id, notice_id, experience_config_id)
            VALUES (:record_id, :notice_id, :experience_config_id)
            """
        )
        for notice_id in row["id"]:
            bind.execute(
                link_notice_query,
                {
                    "record_id": generate_record_id("exp"),
                    "notice_id": notice_id,
                    "experience_config_id": row["experience_config_id_after"],
                },
            )

    # Add ExperienceNotice entries, effectively linking notices to experiences
    experience_config_df.apply(link_notices_to_experiences, axis=1)

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
                "language": "en_us",
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


def downgrade():
    pass
    # ### commands auto generated by Alembic - please adjust! ###
