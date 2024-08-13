/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CurrentStep } from './CurrentStep';
import type { ManualAction } from './ManualAction';

/**
 * Describes actions needed on a particular checkpoint.
 *
 * Examples are a paused collection that needs manual input, a failed collection that
 * needs to be restarted, or a collection where instructions need to be emailed to a third
 * party to complete the request.
 */
export type CheckpointActionRequiredDetails = {
  step: CurrentStep;
  collection?: string;
  action_needed?: Array<ManualAction>;
};

