/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomTaxonomyColor } from './CustomTaxonomyColor';

/**
 * Schema for creating system group entities.
 */
export type SystemGroupCreate = {
  /**
   * A unique key used to identify this resource
   */
  fides_key?: (string | null);
  /**
   * Human-readable name for this resource
   */
  name: string;
  /**
   * A detailed description of what this resource is
   */
  description?: (string | null);
  /**
   * The parent key for hierarchical relationships
   */
  parent_key?: (string | null);
  /**
   * Whether the resource is active
   */
  active?: (boolean | null);
  /**
   * Optional color label for the group
   */
  label_color?: (CustomTaxonomyColor | null);
  /**
   * Optional username of the group's steward
   */
  data_steward?: (string | null);
  /**
   * List of DataUse fides_keys associated with the group
   */
  data_uses?: Array<string>;
  /**
   * A list of system fides_keys that are part of this group
   */
  systems?: Array<string>;
};

