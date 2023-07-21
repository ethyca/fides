/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AllowedTypes } from "./AllowedTypes";
import type { ResourceTypes } from "./ResourceTypes";

export type CustomFieldDefinitionResponse = {
  name: string;
  description?: string;
  field_type: AllowedTypes;
  allow_list_id?: string;
  resource_type: ResourceTypes;
  field_definition?: string;
  active?: boolean;
  id: string;
  created_at: string;
};
