/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FidesConsentScopes } from "./FidesConsentScopes";

/**
 * Scope information with reserved 'fides' namespace and arbitrary additional fields
 */
export type ConsentScopeResponse = {
  fides: FidesConsentScopes;
};
