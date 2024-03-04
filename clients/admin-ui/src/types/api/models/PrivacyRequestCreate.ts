/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Consent } from './Consent';
import type { CustomPrivacyRequestField } from './CustomPrivacyRequestField';
import type { Identity } from './Identity';

/**
 * Data required to create a PrivacyRequest
 */
export type PrivacyRequestCreate = {
  external_id?: string;
  started_processing_at?: string;
  finished_processing_at?: string;
  requested_at?: string;
  identity: Identity;
  consent_request_id?: string;
  custom_privacy_request_fields?: Record<string, CustomPrivacyRequestField>;
  policy_key: string;
  encryption_key?: string;
  consent_preferences?: Array<Consent>;
};

