/* istanbul ignore file */
/* tslint:disable */

/**
 * An external representation of a Rule's target DataCategory within a Fidesops Policy
 */
export type RuleTarget = {
  name?: string | null;
  key?: string | null;
  data_category: string;
};
