import {
  ContactDetails,
  FidesBase,
  FidesKey,
} from "~/features/common/fides-types";
import { DatasetCollection, DatasetField } from "~/types/api";

export type { DatasetCollection, DatasetField } from "~/types/api";

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

export interface ColumnMetadata {
  name: string;
  attribute: keyof DatasetField;
}
