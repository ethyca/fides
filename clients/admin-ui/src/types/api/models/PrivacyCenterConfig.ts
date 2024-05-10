/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyRequestOption } from "./PrivacyRequestOption";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type PrivacyCenterConfig = {
  actions: Array<PrivacyRequestOption>;
};
