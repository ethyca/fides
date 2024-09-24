/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Consent } from "./Consent";
import type { fides__api__schemas__redis_cache__CustomPrivacyRequestField } from "./fides__api__schemas__redis_cache__CustomPrivacyRequestField";
import type { Identity } from "./Identity";
import type { PrivacyRequestSource } from "./PrivacyRequestSource";

/**
 * Data required to create a PrivacyRequest
 */
export type PrivacyRequestCreate = {
  external_id?: string | null;
  started_processing_at?: string | null;
  finished_processing_at?: string | null;
  requested_at?: string | null;
  identity: Identity;
  consent_request_id?: string | null;
  custom_privacy_request_fields?: Record<
    string,
    fides__api__schemas__redis_cache__CustomPrivacyRequestField
  > | null;
  policy_key: string;
  encryption_key?: string | null;
  property_id?: string | null;
  consent_preferences?: Array<Consent> | null;
  source?: PrivacyRequestSource | null;
};
