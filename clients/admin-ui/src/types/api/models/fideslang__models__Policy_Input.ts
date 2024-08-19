/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PolicyRule_Input } from "./PolicyRule_Input";

/**
 * The Policy resource model.
 *
 * An object used to organize a list of PolicyRules.
 */
export type fideslang__models__Policy_Input = {
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
  /**
   *
   * The PolicyRule resource model.
   *
   * Describes the allowed combination of the various privacy data types.
   *
   */
  rules: Array<PolicyRule_Input>;
};
