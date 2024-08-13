/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExtendedIdentityTypes } from "./ExtendedIdentityTypes";

/**
 * Overrides base AdvancedSettings to have extended IdentityTypes
 */
export type AdvancedSettingsWithExtendedIdentityTypes = {
  identity_types: ExtendedIdentityTypes;
};
