/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DataSubjectRights } from './DataSubjectRights';

/**
 * The DataSubject resource model.
 */
export type DataSubject = {
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
  /**
   *
   * The DataSubjectRights resource model.
   *
   * Includes a strategy and optionally a
   * list of data subject rights to apply
   * via the set strategy.
   *
   */
  rights?: DataSubjectRights;
  /**
   * A boolean value to annotate whether or not automated decisions/profiling exists for the data subject.
   */
  automated_decisions_or_profiling?: boolean;
  /**
   * Indicates whether the resource is currently 'active'.
   */
  active?: boolean;
};

