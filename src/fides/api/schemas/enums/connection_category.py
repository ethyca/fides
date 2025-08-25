from enum import Enum


class ConnectionCategory(str, Enum):
    """
    Categories for connection types, matching frontend ConnectionCategory enum
    """

    DATA_CATALOG = "DATA_CATALOG"
    DATA_WAREHOUSE = "DATA_WAREHOUSE"
    DATABASE = "DATABASE"
    IDENTITY_PROVIDER = "IDENTITY_PROVIDER"
    WEBSITE = "WEBSITE"
    CRM = "CRM"
    MANUAL = "MANUAL"
    MARKETING = "MARKETING"
    ANALYTICS = "ANALYTICS"
    ECOMMERCE = "ECOMMERCE"
    COMMUNICATION = "COMMUNICATION"
    CUSTOM = "CUSTOM"  # Fallback for uncategorized/custom uploaded integrations
