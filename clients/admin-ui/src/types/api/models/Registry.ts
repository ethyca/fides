/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The Registry resource model.
 *
 * Systems can be assigned to this resource, but it doesn't inherently
 * point to any other resources.
 */
export type Registry = {
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
};
