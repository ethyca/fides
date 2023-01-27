/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ResourceTypes } from "./ResourceTypes";

export type CustomFieldWithId = {
  resource_type: ResourceTypes;
  resource_id: string;
  custom_field_definition_id: string;
  value: string | Array<string>;
  id?: string;
};
