/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for taxonomy resources.
 */
export type TaxonomyResponse = {
  /**
   * Taxonomy type key
   */
  fides_key: string;
  /**
   * Display name for the taxonomy
   */
  name?: string | null;
  /**
   * Taxonomy description
   */
  description?: string | null;
  /**
   * List of resource types this taxonomy can be applied to
   */
  applies_to?: Array<string>;
};
