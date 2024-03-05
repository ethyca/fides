/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A summary of privacy declaration information for a system aggregated by TCF purpose.
 */
export type SystemPurposeSummary = {
  fides_key: string;
  name: string;
  purposes: Record<string, Record<string, Array<any>>>;
  features: Array<string>;
  data_categories: Array<string>;
};
