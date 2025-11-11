/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for updating generic taxonomy elements.
 */
export type TaxonomyElementUpdate = {
  /**
   * Human-readable name for this resource
   */
  name?: string | null;
  /**
   * A detailed description of what this resource is
   */
  description?: string | null;
  /**
   * The parent key for hierarchical relationships
   */
  parent_key?: string | null;
  /**
   * Whether the resource is active
   */
  active?: boolean | null;
};
