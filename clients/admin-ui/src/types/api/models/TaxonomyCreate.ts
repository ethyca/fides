/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for creating a taxonomy.
 */
export type TaxonomyCreate = {
  /**
   * Taxonomy type key to create
   */
  taxonomy_type: string;
  name?: string | null;
  description?: string | null;
  applies_to?: Array<string> | null;
};
