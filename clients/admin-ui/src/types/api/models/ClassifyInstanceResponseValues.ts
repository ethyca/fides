/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ClassificationStatus } from "./ClassificationStatus";
import type { GenerateTypes } from "./GenerateTypes";

export type ClassifyInstanceResponseValues = {
  status: ClassificationStatus;
  organization_key: string;
  dataset_key: string;
  dataset_name: string;
  target: string;
  type: GenerateTypes;
  id: string;
  created_at: string;
  updated_at: string;
  has_labels?: boolean;
};
