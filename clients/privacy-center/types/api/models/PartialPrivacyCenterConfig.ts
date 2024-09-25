/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PartialPrivacyRequestOption } from "./PartialPrivacyRequestOption";

/**
 * Partial schema for the Admin UI privacy request submission.
 */
export type PartialPrivacyCenterConfig = {
  actions: Array<PartialPrivacyRequestOption>;
};
