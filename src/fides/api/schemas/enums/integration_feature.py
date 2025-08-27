from enum import Enum


class IntegrationFeature(str, Enum):
    """
    Features that can be enabled for different integration types.
    These control which tabs and functionality are available in the integration detail view.
    """

    # Enables data discovery and monitoring functionality - shows "Data discovery" tab
    DATA_DISCOVERY = "DATA_DISCOVERY"

    # Enables data synchronization to external systems - shows "Data sync" tab
    DATA_SYNC = "DATA_SYNC"

    # Enables task/workflow management for manual processes - shows "Tasks" tab
    TASKS = "TASKS"

    # Indicates integration doesn't require connection testing - shows "Details" tab instead of "Connection" tab
    WITHOUT_CONNECTION = "WITHOUT_CONNECTION"

    # Enables Data Subject Request automation for SAAS integrations
    DSR_AUTOMATION = "DSR_AUTOMATION"

    # Enables conditions configuration for manual task creation - shows "Conditions" tab
    CONDITIONS = "CONDITIONS"
