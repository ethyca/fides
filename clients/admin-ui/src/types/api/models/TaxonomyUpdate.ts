/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for updating a taxonomy.
 */
export type TaxonomyUpdate = {
  name?: string | null;
  description?: string | null;
  applies_to?: Array<string> | null;
};
