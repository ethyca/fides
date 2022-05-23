import {
  ContactDetails,
  FidesBase,
  FidesKey,
} from "@/features/common/fides-types";

interface DatasetMetadata {
  resource_id?: string;
}

export interface Dataset extends FidesBase {
  meta?: Record<string, string>;
  data_categories?: FidesKey[];
  data_qualifier: FidesKey;
  fidesctl_meta?: DatasetMetadata;
  collections: DatasetCollection[];
  retention?: string;

  joint_controller?: ContactDetails[];
  third_country_transfers?: string[];
}

export interface FidesLangBase {
  name: string;
  description?: string;
  data_categories?: string[];
  data_qualifier: string;
  retention?: string;
  fields: DatasetField[];
}

export interface DatasetField {
  name: string;
  description?: string;
  data_categories?: FidesKey[];
  data_qualifier: FidesKey;
  retention?: string;
  fields?: DatasetField[];
}

export interface DatasetCollection {
  name: string;
  description?: string;
  data_categories?: FidesKey[];
  data_qualifier: FidesKey;
  retention?: string;
  fields: DatasetField[];
}
