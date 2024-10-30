/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CurrentStep } from "./CurrentStep";
import type { ManualAction } from "./ManualAction";

export type CheckpointActionRequiredDetails = {
  step: CurrentStep;
  collection?: string | null;
  action_needed?: Array<ManualAction> | null;
};
