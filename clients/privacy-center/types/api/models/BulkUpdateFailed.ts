/* istanbul ignore file */
/* tslint:disable */

/**
 * Schema for use when Bulk Create/Update fails.
 */
export type BulkUpdateFailed = {
  message: string;
  data: any;
};
