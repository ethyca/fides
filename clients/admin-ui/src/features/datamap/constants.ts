/**
 * Enums
 */

export const CELL_SIZE = 20;

export const DATA_CATEGORY_COLUMN_ID = "unioned_data_categories";

export const ItemTypes = {
  DraggableColumnListItem: "DraggableColumnListItem",
};

export enum ExportFormat {
  csv = "csv",
  xlsx = "xlsx",
}

export const SYSTEM_NAME = "system.name";
export const SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME =
  "system.privacy_declaration.data_use.name";
export const SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME =
  "system.privacy_declaration.data_subjects.name";
export const SYSTEM_DESCRIPTION = "system.description";
export const DATASET_SOURCE_NAME = "dataset.source_name";
export const SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_AUTOMATED_DECISIONS_OR_PROFILING =
  "system.privacy_declaration.data_subjects.automated_decisions_or_profiling";
export const ORGANIZATION_LINK_TO_SECURITY_POLICY =
  "organization.link_to_security_policy";
export const SYSTEM_ADMINISTRATING_DEPARTMENT =
  "system.administrating_department";
export const DATASET_NAME = "dataset.name";
export const SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_RIGHTS_AVAILABLE =
  "system.privacy_declaration.data_subjects.rights_available";
export const SYSTEM_PRIVACY_DECLARATION_NAME =
  "system.privacy_declaration.name";

export const SYSTEM_INGRESS = "system.ingress";
export const SYSTEM_EGRESS = "system.egress";

type NameMap = {
  [column: string]: string;
};

export const COLUMN_NAME_MAP: NameMap = {};

COLUMN_NAME_MAP[SYSTEM_NAME] = "System Name";
COLUMN_NAME_MAP[SYSTEM_DESCRIPTION] = "Description";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME] = "Data Use";
COLUMN_NAME_MAP[DATA_CATEGORY_COLUMN_ID] = "Data Category";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME] = "Data Subject";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_RIGHTS_AVAILABLE] =
  "Data Subject Rights";
COLUMN_NAME_MAP[DATASET_NAME] = "Datasets";
COLUMN_NAME_MAP[SYSTEM_ADMINISTRATING_DEPARTMENT] = "Department";
COLUMN_NAME_MAP[ORGANIZATION_LINK_TO_SECURITY_POLICY] =
  "Data Security Practices";
COLUMN_NAME_MAP[DATASET_SOURCE_NAME] = "Data Source";
COLUMN_NAME_MAP[
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_AUTOMATED_DECISIONS_OR_PROFILING
] = "Purpose for Automated decision-making or profiling";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_NAME] = "Processing Activity";
COLUMN_NAME_MAP[SYSTEM_INGRESS] = "Source Systems";
COLUMN_NAME_MAP[SYSTEM_EGRESS] = "Destination Systems";

// eslint-disable-next-line @typescript-eslint/naming-convention
export enum DATAMAP_LOCAL_STORAGE_KEYS {
  COLUMN_ORDER = "datamap-column-order",
  COLUMN_VISIBILITY = "datamap-column-visibility",
  COLUMN_SIZING = "datamap-column-sizing",
  COLUMN_EXPANSION_STATE = "datamap-column-expansion-state",
  CUSTOM_REPORT_ID = "datamap-custom-report-id",
  FILTERS = "datamap-filters",
  GROUP_BY = "datamap-group-by",
  SORTING_STATE = "datamap-sorting-state",
  WRAPPING_COLUMNS = "datamap-wrapping-columns",
}
