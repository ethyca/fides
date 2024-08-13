/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConditionalValue } from './ConditionalValue';

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type ConfigConsentOption = {
  cookieKeys?: Array<string>;
  default?: (boolean | ConditionalValue);
  description: string;
  fidesDataUseKey: string;
  highlight?: boolean;
  name: string;
  url: string;
  executable?: boolean;
};

