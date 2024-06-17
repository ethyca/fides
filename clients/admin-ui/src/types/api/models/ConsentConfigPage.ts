/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConfigConsentOption } from "./ConfigConsentOption";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type ConsentConfigPage = {
  consentOptions?: Array<ConfigConsentOption>;
  description: string;
  description_subtext?: Array<string>;
  policy_key?: string;
  title: string;
};
