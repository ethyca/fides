/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FidesConsentMetaResponse } from "./FidesConsentMetaResponse";

/**
 * Metadata information with reserved 'fides' namespace and arbitrary additional fields
 */
export type ConsentMetaResponse = {
  fides: FidesConsentMetaResponse;
};
