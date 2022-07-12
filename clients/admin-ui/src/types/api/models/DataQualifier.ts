/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The DataQualifier resource model.
 */
export type DataQualifier = {
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
