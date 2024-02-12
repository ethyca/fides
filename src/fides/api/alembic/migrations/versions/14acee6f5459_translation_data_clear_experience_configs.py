"""translation data

Revision ID: 14acee6f5459
Revises: a1e23b70f2b2
Create Date: 2024-01-09 21:17:13.115020

"""

import uuid

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.

revision = "14acee6f5459"
down_revision = "a1e23b70f2b2"
branch_labels = None
depends_on = None


def generate_record_id(prefix):
    return prefix + "_" + str(uuid.uuid4())


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

    drop_fk_constraint(bind)
    delete_experiences(bind)
    delete_experience_configs(bind)


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
        SET translation_id = noticetranslation.id, title = privacynoticehistory.name, language = "en"
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

    remove_existing_experience_data(bind)

    migrate_notices(bind)


def downgrade():
    # Downgrade will _not_ attempt to recreate PrivacyExperienceConfig recrords,
    # as that should be handled by the (old) server's OOB loading behavior
    bind = op.get_bind()

    downward_migrate_notices(bind)
