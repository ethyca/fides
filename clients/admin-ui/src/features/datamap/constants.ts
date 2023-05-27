/**
 * Enums
 */

export const CELL_SIZE = 20;

export const DATA_CATEGORY_COLUMN_ID = "unioned_data_categories";

export const GRAY_BACKGROUND = "#F7F7F7";

export const ItemTypes = {
  DraggableColumnListItem: "DraggableColumnListItem",
};

export const SYSTEM_FIDES_KEY_COLUMN_ID = "system.fides_key";
export const SYSTEM_NAME = "system.name";
export const SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME =
  "system.privacy_declaration.data_use.name";
export const SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME =
  "system.privacy_declaration.data_subjects.name";
export const SYSTEM_DESCRIPTION = "system.description";
export const SYSTEM_PRIVACY_DECLARATION_DATA_USE_LEGAL_BASIS =
  "system.privacy_declaration.data_use.legal_basis";

export const SYSTEM_DATA_RESPONSIBILITY_TITLE =
  "system.data_responsibility_title";

export const DATASET_SOURCE_NAME = "dataset.source_name";
export const SYSTEM_PRIVACY_DECLARATION_DATA_USE_LEGITIMATE_INTEREST_IMPACT_ASSESSMENT =
  "system.privacy_declaration.data_use.legitimate_interest_impact_assessment";
export const SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_AUTOMATED_DECISIONS_OR_PROFILING =
  "system.privacy_declaration.data_subjects.automated_decisions_or_profiling";
export const SYSTEM_PRIVACY_DECLARATION_DATA_USE_RECIPIENTS =
  "system.privacy_declaration.data_use.recipients";
export const SYSTEM_DATA_PROTECTION_IMPACT_ASSESSMENT_LINK =
  "system.data_protection_impact_assessment.link";
export const SYSTEM_PRIVACY_DECLARATION_DATA_USE_SPECIAL_CATEGORY =
  "system.privacy_declaration.data_use.special_category";
export const ORGANIZATION_LINK_TO_SECURITY_POLICY =
  "organization.link_to_security_policy";
export const SYSTEM_JOINT_CONTROLLER = "system.joint_controller";
export const DATASET_RETENTION = "dataset.retention";
export const SYSTEM_ADMINISTRATING_DEPARTMENT =
  "system.administrating_department";
export const DATASET_NAME = "dataset.name";
export const SYSTEM_SYSTEM_DEPENDENCIES = "system.system_dependencies";
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
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_DATA_USE_LEGAL_BASIS] =
  "Legal Basis";
COLUMN_NAME_MAP[DATA_CATEGORY_COLUMN_ID] = "Data Category";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME] = "Data Subject";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_RIGHTS_AVAILABLE] =
  "Data Subject Rights";
COLUMN_NAME_MAP[DATASET_NAME] = "Datasets";
COLUMN_NAME_MAP[SYSTEM_ADMINISTRATING_DEPARTMENT] = "Department";
COLUMN_NAME_MAP[SYSTEM_DATA_RESPONSIBILITY_TITLE] = "Responsibility";
COLUMN_NAME_MAP[SYSTEM_JOINT_CONTROLLER] = "Joint Controller";
COLUMN_NAME_MAP[DATASET_RETENTION] = "Retention Period";
COLUMN_NAME_MAP[ORGANIZATION_LINK_TO_SECURITY_POLICY] =
  "Data Security Practices";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_DATA_USE_SPECIAL_CATEGORY] =
  "Legal Basis for Special Category Data";
COLUMN_NAME_MAP[SYSTEM_DATA_PROTECTION_IMPACT_ASSESSMENT_LINK] =
  "Data Protection Impact Assessment";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_DATA_USE_RECIPIENTS] =
  "Third Party Recipients";
COLUMN_NAME_MAP[DATASET_SOURCE_NAME] = "Data Source";
COLUMN_NAME_MAP[
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_AUTOMATED_DECISIONS_OR_PROFILING
] = "Purpose for Automated decision-making or profiling";
COLUMN_NAME_MAP[
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_LEGITIMATE_INTEREST_IMPACT_ASSESSMENT
] = "Legitimate Interests Assessment";
COLUMN_NAME_MAP[SYSTEM_PRIVACY_DECLARATION_NAME] = "Processing Activity";
COLUMN_NAME_MAP[SYSTEM_INGRESS] = "Source Systems";
COLUMN_NAME_MAP[SYSTEM_EGRESS] = "Destination Systems";
// COLUMN_NAME_MAP[] = 'Data Steward'; #  needs to be added in backend
// COLUMN_NAME_MAP[] = 'Geography'; # needs to be added in backend
// COLUMN_NAME_MAP[] = 'Tags'; # couldn't find it
// COLUMN_NAME_MAP[] = 'Third Party Categories'; #new
// COLUMN_NAME_MAP[] = 'Data Protection [Impact] Assessment (DPA/DPIA)'; #new
// COLUMN_NAME_MAP[] = 'Legal basis for International Transfer'; #new;
// COLUMN_NAME_MAP[] = 'Cookies'; #new;
// COLUMN_NAME_MAP[] = 'Consent Notice'; #new;
// COLUMN_NAME_MAP[] = 'Legal Name & Address'; #new;
// COLUMN_NAME_MAP[] = 'Privacy Policy'; #new;
// COLUMN_NAME_MAP[] = 'Data Protection Officer (DPO)'; #new;
