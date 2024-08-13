/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ProviderEnum } from "./ProviderEnum";

/**
 * Simple schema display providers in the login page.
 */
export type OpenIDProviderSimple = {
  name: string;
  identifier: string;
  provider: ProviderEnum;
};
