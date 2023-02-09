/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FidesDataCategory } from "./FidesDataCategory";

/**
 * An external representation of a Rule's target DataCategory within a Fidesops Policy
 */
export type RuleTarget = {
  name?: string;
  key?: string;
  data_category: FidesDataCategory;
};
