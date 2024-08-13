/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The DataUse resource model.
 */
export type DataUse = {
  /**
   * The version of Fideslang in which this label was added.
   */
  version_added?: string;
  /**
   * The version of Fideslang in which this label was deprecated.
   */
  version_deprecated?: string;
  /**
   * The new name, if applicable, for this label after deprecation.
   */
  replaced_by?: string;
  /**
   * Denotes whether the resource is part of the default taxonomy or not.
   */
  is_default?: boolean;
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
   * Indicates whether the resource is currently 'active'.
   */
  active?: boolean;
};
