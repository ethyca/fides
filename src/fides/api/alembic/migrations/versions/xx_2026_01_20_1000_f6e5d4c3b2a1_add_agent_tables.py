"""add agent tables for AI assistant

Revision ID: f6e5d4c3b2a1
Revises: 6d5f70dd0ba5
Create Date: 2026-01-20 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f6e5d4c3b2a1"
down_revision = "6d5f70dd0ba5"
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension for vector embeddings
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Create agent_settings table (singleton for org-level settings)
    op.create_table(
        "agent_settings",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "compliance_frameworks",
            postgresql.ARRAY(sa.String()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("custom_system_prompt", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_settings_id"), "agent_settings", ["id"], unique=False)

    # Create agent_conversation table
    op.create_table(
        "agent_conversation",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("is_archived", sa.Boolean(), server_default="false", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["fidesuser.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_conversation_id"), "agent_conversation", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_agent_conversation_user_id"),
        "agent_conversation",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_conversation_created_at"),
        "agent_conversation",
        ["created_at"],
        unique=False,
    )

    # Create agent_message table
    op.create_table(
        "agent_message",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("conversation_id", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
        ),  # 'user', 'assistant', 'tool'
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "tool_calls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),  # Tool calls made by assistant
        sa.Column(
            "tool_call_id", sa.String(length=255), nullable=True
        ),  # For tool response messages
        sa.Column("model_used", sa.String(length=100), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["agent_conversation.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_message_id"), "agent_message", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_agent_message_conversation_id"),
        "agent_message",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_message_created_at"),
        "agent_message",
        ["created_at"],
        unique=False,
    )

    # Create agent_embedding table with vector column
    # Using 768 dimensions for text-embedding-004
    op.create_table(
        "agent_embedding",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_embedding_id"), "agent_embedding", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_agent_embedding_entity_type"),
        "agent_embedding",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_embedding_entity_id"),
        "agent_embedding",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_embedding_entity_type_entity_id",
        "agent_embedding",
        ["entity_type", "entity_id"],
        unique=True,
    )

    # Add the vector column using raw SQL (pgvector specific)
    op.execute(
        "ALTER TABLE agent_embedding ADD COLUMN embedding vector(768);"
    )
    # Create an IVFFlat index for fast similarity search
    op.execute(
        "CREATE INDEX ix_agent_embedding_vector ON agent_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    )

    # Create agent_embedding_queue table for async embedding updates
    op.create_table(
        "agent_embedding_queue",
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column(
            "operation",
            sa.String(length=20),
            nullable=False,
        ),  # 'insert', 'update', 'delete'
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("entity_type", "entity_id"),
    )
    op.create_index(
        op.f("ix_agent_embedding_queue_created_at"),
        "agent_embedding_queue",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_embedding_queue_processed_at"),
        "agent_embedding_queue",
        ["processed_at"],
        unique=False,
    )

    # Create function to queue embedding updates
    op.execute(
        """
        CREATE OR REPLACE FUNCTION queue_embedding_update()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                INSERT INTO agent_embedding_queue (entity_type, entity_id, operation)
                VALUES (TG_ARGV[0], OLD.id, 'delete')
                ON CONFLICT (entity_type, entity_id)
                DO UPDATE SET operation = 'delete', created_at = now(), processed_at = NULL;
                RETURN OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO agent_embedding_queue (entity_type, entity_id, operation)
                VALUES (TG_ARGV[0], NEW.id, 'update')
                ON CONFLICT (entity_type, entity_id)
                DO UPDATE SET operation = 'update', created_at = now(), processed_at = NULL;
                RETURN NEW;
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO agent_embedding_queue (entity_type, entity_id, operation)
                VALUES (TG_ARGV[0], NEW.id, 'insert')
                ON CONFLICT (entity_type, entity_id)
                DO UPDATE SET operation = 'insert', created_at = now(), processed_at = NULL;
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Create triggers for each entity type to queue embedding updates
    # ctl_organizations
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_organization
        AFTER INSERT OR UPDATE OR DELETE ON ctl_organizations
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('organization');
        """
    )

    # ctl_systems
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_system
        AFTER INSERT OR UPDATE OR DELETE ON ctl_systems
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('system');
        """
    )

    # ctl_datasets
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_dataset
        AFTER INSERT OR UPDATE OR DELETE ON ctl_datasets
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('dataset');
        """
    )

    # privacydeclaration
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_privacy_declaration
        AFTER INSERT OR UPDATE OR DELETE ON privacydeclaration
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('privacy_declaration');
        """
    )

    # privacynotice
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_privacy_notice
        AFTER INSERT OR UPDATE OR DELETE ON privacynotice
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('privacy_notice');
        """
    )

    # privacyexperience
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_privacy_experience
        AFTER INSERT OR UPDATE OR DELETE ON privacyexperience
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('privacy_experience');
        """
    )

    # connectionconfig
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_connection_config
        AFTER INSERT OR UPDATE OR DELETE ON connectionconfig
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('connection_config');
        """
    )

    # stagedresource
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_staged_resource
        AFTER INSERT OR UPDATE OR DELETE ON stagedresource
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('staged_resource');
        """
    )

    # monitorconfig
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_discovery_monitor
        AFTER INSERT OR UPDATE OR DELETE ON monitorconfig
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('discovery_monitor');
        """
    )

    # policy (DSR policies)
    op.execute(
        """
        CREATE TRIGGER agent_embedding_queue_policy
        AFTER INSERT OR UPDATE OR DELETE ON policy
        FOR EACH ROW EXECUTE FUNCTION queue_embedding_update('policy');
        """
    )


def downgrade():
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS agent_embedding_queue_policy ON policy;")
    op.execute(
        "DROP TRIGGER IF EXISTS agent_embedding_queue_discovery_monitor ON monitorconfig;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS agent_embedding_queue_staged_resource ON stagedresource;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS agent_embedding_queue_connection_config ON connectionconfig;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS agent_embedding_queue_privacy_experience ON privacyexperience;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS agent_embedding_queue_privacy_notice ON privacynotice;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS agent_embedding_queue_privacy_declaration ON privacydeclaration;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS agent_embedding_queue_dataset ON ctl_datasets;"
    )
    op.execute("DROP TRIGGER IF EXISTS agent_embedding_queue_system ON ctl_systems;")
    op.execute(
        "DROP TRIGGER IF EXISTS agent_embedding_queue_organization ON ctl_organizations;"
    )

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS queue_embedding_update();")

    # Drop tables
    op.drop_index(
        op.f("ix_agent_embedding_queue_processed_at"),
        table_name="agent_embedding_queue",
    )
    op.drop_index(
        op.f("ix_agent_embedding_queue_created_at"),
        table_name="agent_embedding_queue",
    )
    op.drop_table("agent_embedding_queue")

    op.drop_index("ix_agent_embedding_vector", table_name="agent_embedding")
    op.drop_index(
        "ix_agent_embedding_entity_type_entity_id", table_name="agent_embedding"
    )
    op.drop_index(op.f("ix_agent_embedding_entity_id"), table_name="agent_embedding")
    op.drop_index(op.f("ix_agent_embedding_entity_type"), table_name="agent_embedding")
    op.drop_index(op.f("ix_agent_embedding_id"), table_name="agent_embedding")
    op.drop_table("agent_embedding")

    op.drop_index(op.f("ix_agent_message_created_at"), table_name="agent_message")
    op.drop_index(
        op.f("ix_agent_message_conversation_id"), table_name="agent_message"
    )
    op.drop_index(op.f("ix_agent_message_id"), table_name="agent_message")
    op.drop_table("agent_message")

    op.drop_index(
        op.f("ix_agent_conversation_created_at"), table_name="agent_conversation"
    )
    op.drop_index(
        op.f("ix_agent_conversation_user_id"), table_name="agent_conversation"
    )
    op.drop_index(op.f("ix_agent_conversation_id"), table_name="agent_conversation")
    op.drop_table("agent_conversation")

    op.drop_index(op.f("ix_agent_settings_id"), table_name="agent_settings")
    op.drop_table("agent_settings")

    # Note: We don't drop the pgvector extension as it may be used by other features
