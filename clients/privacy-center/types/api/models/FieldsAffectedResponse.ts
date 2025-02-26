/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema detailing the individual fields affected by a particular query detailed in the ExecutionLog
 */
export type FieldsAffectedResponse = {
  path: string | null;
  field_name: string | null;
  data_categories: Array<string> | null;
};
