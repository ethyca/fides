/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Consent } from './Consent';
import type { ConsentWithExecutableStatus } from './ConsentWithExecutableStatus';
import type { Identity } from './Identity';

/**
 * Schema for consent preferences including the verification code.
 */
export type ConsentPreferencesWithVerificationCode = {
  code?: string;
  consent: Array<Consent>;
  policy_key?: string;
  executable_options?: Array<ConsentWithExecutableStatus>;
  browser_identity?: Identity;
};
