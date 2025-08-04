from enum import Enum


class ConnectionCategory(str, Enum):
    """
    Categories for connection types, matching frontend ConnectionCategory enum
    """

    DATA_CATALOG = "Data Catalog"
    DATA_WAREHOUSE = "Data Warehouse"
    DATABASE = "Database"
    IDENTITY_PROVIDER = "Identity Provider"
    WEBSITE = "Website"
    CRM = "CRM"
    MANUAL = "Manual"
    MARKETING = "Marketing"
    ANALYTICS = "Analytics"
    ECOMMERCE = "E-commerce"  # Includes payments and commerce platforms
    COMMUNICATION = "Communication"
    CUSTOM = "Custom"  # Fallback for uncategorized integrations
