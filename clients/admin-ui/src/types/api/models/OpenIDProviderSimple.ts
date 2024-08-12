/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ProviderEnum } from "./ProviderEnum";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type OpenIDProviderSimple = {
  name: string;
  identifier: string;
  provider: ProviderEnum;
};
