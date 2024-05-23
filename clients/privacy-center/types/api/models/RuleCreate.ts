/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { PolicyMaskingSpec } from "./PolicyMaskingSpec";

/**
 * The schema to use when creating a Rule. This schema accepts a storage_destination_key
 * over a composite object.
 */
export type RuleCreate = {
  name: string;
  key?: string;
  action_type: ActionType;
  storage_destination_key?: string;
  masking_strategy?: PolicyMaskingSpec;
};
