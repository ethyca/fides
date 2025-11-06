/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for generic taxonomy elements.
 */
export type TaxonomyElement = {
  /**
   * A unique key used to identify this resource
   */
  fides_key: string;
  /**
   * Human-readable name for this resource
   */
  name?: string;
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
  active?: boolean;
};
