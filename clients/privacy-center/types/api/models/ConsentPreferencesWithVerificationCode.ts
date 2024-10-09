/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Consent } from "./Consent";
import type { ConsentWithExecutableStatus } from "./ConsentWithExecutableStatus";
import type { Identity } from "./Identity";

/**
 * Schema for consent preferences including the verification code.
 */
export type ConsentPreferencesWithVerificationCode = {
  code?: string | null;
  consent: Array<Consent>;
  policy_key?: string | null;
  executable_options?: Array<ConsentWithExecutableStatus> | null;
  browser_identity?: Identity | null;
};
