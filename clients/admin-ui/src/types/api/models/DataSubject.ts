/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DataSubjectRights } from './DataSubjectRights';

/**
 * The DataSubject resource model.
 */
export type DataSubject = {
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
};
