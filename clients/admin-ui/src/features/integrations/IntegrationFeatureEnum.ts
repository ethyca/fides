/**
 * Enum defining the features that can be enabled for different integration types.
 * These features control which tabs and functionality are available in the integration detail view.
 */
export enum IntegrationFeatureEnum {
  /** Enables data discovery and monitoring functionality - shows "Data discovery" tab */
  DATA_DISCOVERY = "data_discovery",

  /** Enables data synchronization to external systems - shows "Data sync" tab */
  DATA_SYNC = "data_sync",

  /** Enables task/workflow management for manual processes - shows "Tasks" tab (currently hidden) */
  TASKS = "tasks",

  /** Indicates integration doesn't require connection testing - shows "Details" tab instead of "Connection" tab */
  WITHOUT_CONNECTION = "without_connection",
}
