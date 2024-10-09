/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { PolicyMaskingSpecResponse } from "./PolicyMaskingSpecResponse";
import type { RuleTarget } from "./RuleTarget";
import type { StorageDestinationResponse } from "./StorageDestinationResponse";

/**
 * The schema to use when returning a Rule via the API and when including the Rule's targets
 * is desired. This schema uses a censored version of the `PolicyMaskingSpec` that omits the
 * configuration to avoid exposing secrets.
 */
export type RuleResponseWithTargets = {
  name: string;
  key?: string | null;
  action_type: ActionType;
  targets?: Array<RuleTarget> | null;
  storage_destination?: StorageDestinationResponse | null;
  masking_strategy?: PolicyMaskingSpecResponse | null;
};
