/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConditionalValue } from "./ConditionalValue";

export type ConfigConsentOption = {
  cookieKeys?: Array<string>;
  default?: boolean | ConditionalValue | null;
  description: string;
  fidesDataUseKey: string;
  highlight?: boolean | null;
  name: string;
  url: string;
  executable?: boolean | null;
};
