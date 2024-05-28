"""property specific messaging migration data


Revision ID: 5f96f13be8ec
Revises: 2736c942faa2
Create Date: 2024-05-28 14:52:08.114674

"""

import random
import string
import uuid
from typing import Dict, Any

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from fides.api.schemas.messaging.messaging import MessagingActionType
from sqlalchemy.exc import IntegrityError

from sqlalchemy import text
from sqlalchemy.engine import Connection, ResultProxy
from sqlalchemy.sql.elements import TextClause


# revision identifiers, used by Alembic.
revision = "5f96f13be8ec"
down_revision = "2736c942faa2"
branch_labels = None
depends_on = None


DEFAULT_MESSAGING_TEMPLATES: Dict[str, Any] = {
    MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value: {
        "label": "Subject identity verification",
        "content": {
            "subject": "Your one-time code is {{code}}",
            "body": "Your privacy request verification code is {{code}}. Please return to the Privacy Center and enter the code to continue. This code will expire in {{minutes}} minutes.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_RECEIPT.value: {
        "label": "Privacy request received",
        "content": {
            "subject": "Your privacy request has been received",
            "body": "Your privacy request has been received. We will get back to you shortly.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE.value: {
        "label": "Privacy request approved",
        "content": {
            "subject": "Your privacy request has been approved",
            "body": "Your privacy request has been approved and is currently processing.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY.value: {
        "label": "Privacy request denied",
        "content": {
            "subject": "Your privacy request has been denied",
            "body": "Your privacy request has been denied. {{denial_reason}}.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS.value: {
        "label": "Access request completed",
        "content": {
            "subject": "Your data is ready to be downloaded",
            "body": "Your access request has been completed and can be downloaded at {{download_link}}. For security purposes, this secret link will expire in {{days}} days.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION.value: {
        "label": "Erasure request completed",
        "content": {
            "subject": "Your data has been deleted",
            "body": "Your erasure request has been completed.",
        },
    },
}

AUTO_MIGRATED_STRING = "auto-migrated"


def generate_record_id(prefix):
    return prefix + "_" + str(uuid.uuid4())


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind: Connection = op.get_bind()

    # STEP 1: Ensure we have exactly 1 default property in the DB
    existing_properties: ResultProxy = bind.execute(
        text("select id from plus_property;")
    )
    # todo- what's the right way to get count of rows that's performant?
    if len(existing_properties.all()) == 1:
        # If exactly one property exists, assume this is the "default"
        default_property_id = existing_properties.first()["id"]
        update_property_query: TextClause = text(
            "UPDATE plus_property SET is_default= TRUE WHERE id= :id"
        )
        bind.execute(
            update_property_query,
            {"id": existing_properties.first()["id"]},
        )
    else:
        # Create new property, label as default
        insert_into_property_query: TextClause = text(
            "INSERT INTO plus_property (id, name, is_default, type)"
            "VALUES (:id, :name, :is_default, :type)"
        )
        characters = string.ascii_uppercase + string.digits
        # fixme- does this need the plu_ prefix?
        new_property_id: str = "plu_FDS-" + "".join(random.choices(characters, k=6))
        default_property_id = new_property_id

        new_property: Dict[str, Any] = {
            "id": new_property_id,
            "name": "Default Property",
            "is_default": True,
            "type": "Website",
        }
        try:
            bind.execute(insert_into_property_query, new_property)
        except IntegrityError as exc:
            raise Exception(
                f"Fides attempted to create a new default property but got error: {exc}. "
                f"Adjust keys in property table to not conflict."
            )

    # STEP 2: Ensure all default templates are saved to the DB
    existing_templates: ResultProxy = bind.execute(
        text("select id, type from messaging_template;")
    )
    templates_from_db = [template.type for template in existing_templates.all()]
    for template_type, template in DEFAULT_MESSAGING_TEMPLATES.items():
        # if a template is not already in the DB, save it with defaults
        if template_type not in templates_from_db:
            insert_into_messaging_template_query: TextClause = text(
                "INSERT INTO messaging_template (id, type, content, is_enabled)"
                "VALUES (:id, :type, :content, :is_enabled)"
            )
            new_messaging_template: Dict[str, Any] = {
                "id": generate_record_id("mes"),
                "type": template_type,
                "content": template["content"],
                "is_enabled": False,
            }
            try:
                bind.execute(
                    insert_into_messaging_template_query, new_messaging_template
                )
            except IntegrityError as exc:
                raise Exception(
                    f"Fides attempted to create a new messaging_template but got error: {exc}. "
                )

    # STEP 3: Ensure all saved messaging templates are linked to the default property
    updated_templates: ResultProxy = bind.execute(
        text("select id, type from messaging_template;")
    )
    for template in updated_templates:
        insert_into_messaging_template_to_property_query: TextClause = text(
            "INSERT INTO messaging_template_to_property (id, messaging_template_id, property_id)"
            "VALUES (:id, :messaging_template_id, :property_id)"
        )
        new_messaging_template_to_property: Dict[str, Any] = {
            "id": generate_record_id("mes"),
            "messaging_template_id": template["id"],
            "property_id": default_property_id,
        }
        bind.execute(
            insert_into_messaging_template_to_property_query,
            new_messaging_template_to_property,
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Reverse data migration: remove templates that were automatically created by the forward migration
    bind = op.get_bind()
    bind.execute(text("DELETE * FROM messaging_template_to_property;"))
    bind.execute(text("DELETE FROM messaging_template WHERE is_enabled = FALSE;"))
    # ### end Alembic commands ###
