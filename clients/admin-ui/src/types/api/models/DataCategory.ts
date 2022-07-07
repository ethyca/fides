/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The DataCategory resource model.
 */
export type DataCategory = {
  /**
   * A unique key used to identify this resource.
   */
  fides_key: string;
  /**
   * Defines the Organization that this resource belongs to.
   */
  organization_fides_key?: string;
  /**
   * Human-Readable name for this resource.
   */
  name?: string;
  /**
   * A detailed description of what this resource is.
   */
  description?: string;
  parent_key?: string;
};
