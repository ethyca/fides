import {
  ContactDetails,
  FidesBase,
  FidesKey,
} from "~/features/common/fides-types";

export interface System extends FidesBase {
  registry_id?: number;
  meta?: { tags: string | undefined };
  fidesctl_meta?: SystemMetadata;
  system_type: string;
  data_responsibility_title: DataResponsibilityTitle;
  privacy_declarations: PrivacyDeclaration[];
  system_dependencies?: FidesKey[];
  joint_controller?: ContactDetails[];
  third_country_transfers?: string[];
  administrating_department?: string;
  data_protection_impact_assessment: DataProtectionImpactAssessment;
}

type DataResponsibilityTitle = "Controller" | "Processor" | "Sub-Processor";

interface SystemMetadata {
  resource_id?: string;
  endpoint_address?: string;
  endpoint_port?: string;
}

export interface PrivacyDeclaration {
  name: string;
  data_categories: FidesKey[];
  data_use: FidesKey;
  data_qualifier: FidesKey;
  data_subjects: FidesKey[];
  dataset_references?: FidesKey[];
}

interface DataProtectionImpactAssessment {
  is_required: boolean;
  progress?: string;
  link?: string;
}
