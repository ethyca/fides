/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Consent } from "./Consent";
import type { Identity } from "./Identity";

/**
 * Data required to create a PrivacyRequest
 */
export type PrivacyRequestCreate = {
  external_id?: string;
  started_processing_at?: string;
  finished_processing_at?: string;
  requested_at?: string;
  identity: Identity;
  policy_key: string;
  encryption_key?: string;
  consent_preferences?: Array<Consent>;
};
