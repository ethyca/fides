/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConfigConsentOption } from "./ConfigConsentOption";

export type ConsentConfigPage_Output = {
  consentOptions?: Array<ConfigConsentOption>;
  description: string;
  description_subtext?: Array<string> | null;
  policy_key?: string | null;
  title: string;
};
