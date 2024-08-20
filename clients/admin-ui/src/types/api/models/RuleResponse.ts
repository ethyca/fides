/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { PolicyMaskingSpecResponse } from "./PolicyMaskingSpecResponse";
import type { StorageDestinationResponse } from "./StorageDestinationResponse";

/**
 * The schema to use when returning a Rule via the API. This schema uses a censored version
 * of the `PolicyMaskingSpec` that omits the configuration to avoid exposing secrets.
 */
export type RuleResponse = {
  name: string;
  key?: string | null;
  action_type: ActionType;
  storage_destination?: StorageDestinationResponse | null;
  masking_strategy?: PolicyMaskingSpecResponse | null;
};
