/**
 * This file is an adaptation of the Fideslang and Fidesctl models.py files
 */

type FidesKey = string;

interface FidesBase {
  fides_key: FidesKey;
  organization_fides_key: string;
  name: string;
  description: string;
  // TODO: what date library should we use? once we decide, change this type
  created_at: string;
  updated_at: string;
}

interface DatasetMetadata {
  resource_id?: string;
}

interface ContactDetails {
  name: string;
  address: string;
  email: string;
  phone: string;
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

export interface DatasetCollection extends FidesLangBase {}

export interface DatasetField extends FidesLangBase {}
