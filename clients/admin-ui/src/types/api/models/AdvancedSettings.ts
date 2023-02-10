/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CookieIds } from "./CookieIds";
import type { IdentityTypes } from "./IdentityTypes";

export type AdvancedSettings = {
  identity_types?: Array<IdentityTypes>;
  browser_identity_types?: Array<CookieIds>;
};
