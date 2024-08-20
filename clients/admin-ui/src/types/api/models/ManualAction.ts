/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Surface how to retrieve or mask data in a database-agnostic way
 *
 * - 'locators' are similar to the SQL "WHERE" information.
 * - 'get' contains a list of fields that should be retrieved from the source
 * - 'update' is a dictionary of fields and the replacement value/masking strategy
 */
export type ManualAction = {
  locators: any;
  get: Array<string> | null;
  update: null;
};
