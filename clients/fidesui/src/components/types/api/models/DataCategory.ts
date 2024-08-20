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
  tags?: Array<string> | null;
  /**
   * Human-Readable name for this resource.
   */
  name?: string | null;
  /**
   * A detailed description of what this resource is.
   */
  description?: string | null;
  parent_key?: string | null;
  /**
   * Denotes whether the resource is part of the default taxonomy or not.
   */
  is_default?: boolean;
};
