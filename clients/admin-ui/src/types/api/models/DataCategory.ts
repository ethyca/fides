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
  tags?: Array<string>;
  /**
   * Human-Readable name for this resource.
   */
  name?: string;
  /**
   * A detailed description of what this resource is.
   */
  description?: string;
  parent_key?: string;
  /**
   * Denotes whether the resource is part of the default taxonomy or not.
   */
  is_default?: boolean;
  /**
   * Indicates whether the resource is currently 'active'.
   */
  active?: boolean;
  /**
   * This is for tracking when the default entity was added
   */
  version_added?: string;
  /**
   * This is for tracking when the default entity was deprecated
   */
  version_deprecated?: string;
  /**
   * This is for tracking which default entity was used to replace this resource
   */
  replaced_by?: string;
};
