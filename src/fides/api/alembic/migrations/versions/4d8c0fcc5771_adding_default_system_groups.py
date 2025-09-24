"""adding default system groups

Revision ID: 4d8c0fcc5771
Revises: 5fa78b1f324d
Create Date: 2025-09-10 05:40:19.064377

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "4d8c0fcc5771"
down_revision = "5fa78b1f324d"
branch_labels = None
depends_on = None


def upgrade():
    # Insert default system groups into taxonomy_element table
    op.execute(
        """
        INSERT INTO taxonomy_element (id, created_at, updated_at, taxonomy_type, fides_key, name, description, parent_key, active, tags, organization_fides_key)
        VALUES
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'analytics_business_intelligence', 'Analytics & Business intelligence', 'System group for analytics and business intelligence systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'customer_management', 'Customer management', 'System group for customer management systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'internal_operations', 'Internal operations', 'System group for internal operations systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'legal_compliance', 'Legal & Compliance', 'System group for legal and compliance systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'marketing', 'Marketing', 'System group for marketing systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'payments_billing', 'Payments & Billing', 'System group for payments and billing systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'product_service_delivery', 'Product & Service delivery', 'System group for product and service delivery systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'research_development', 'Research & Development', 'System group for research and development systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'sales_revenue_operations', 'Sales & Revenue operations', 'System group for sales and revenue operations systems', NULL, true, NULL, 'default_organization'),
          ('tax_' || gen_random_uuid(), now(), now(), 'system_group', 'security_fraud', 'Security & Fraud', 'System group for security and fraud systems', NULL, true, NULL, 'default_organization')
        """
    )

    # Insert default system groups into system_group table with white labels
    op.execute(
        """
        INSERT INTO system_group (id, created_at, updated_at, fides_key, label_color, data_steward_username, data_uses)
        VALUES
          ('sys_' || gen_random_uuid(), now(), now(), 'analytics_business_intelligence', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'customer_management', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'internal_operations', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'legal_compliance', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'marketing', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'payments_billing', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'product_service_delivery', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'research_development', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'sales_revenue_operations', 'taxonomy_white', NULL, '{}'),
          ('sys_' || gen_random_uuid(), now(), now(), 'security_fraud', 'taxonomy_white', NULL, '{}')
        """
    )


def downgrade():
    # Remove default system groups from both tables
    op.execute(
        """
        DELETE FROM system_group
        WHERE fides_key IN (
          'analytics_business_intelligence', 'customer_management', 'internal_operations',
          'legal_compliance', 'marketing', 'payments_billing', 'product_service_delivery',
          'research_development', 'sales_revenue_operations', 'security_fraud'
        )
        """
    )

    op.execute(
        """
        DELETE FROM taxonomy_element
        WHERE fides_key IN (
          'analytics_business_intelligence', 'customer_management', 'internal_operations',
          'legal_compliance', 'marketing', 'payments_billing', 'product_service_delivery',
          'research_development', 'sales_revenue_operations', 'security_fraud'
        ) AND taxonomy_type = 'system_group'
        """
    )
