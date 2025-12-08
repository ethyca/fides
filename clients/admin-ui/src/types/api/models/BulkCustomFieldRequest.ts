/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomFieldWithId } from "./CustomFieldWithId";
import type { ResourceTypes } from "./ResourceTypes";

export type BulkCustomFieldRequest = {
  resource_type: ResourceTypes | string;
  resource_id: string;
  upsert?: Array<CustomFieldWithId> | null;
  delete?: Array<string> | null;
};
