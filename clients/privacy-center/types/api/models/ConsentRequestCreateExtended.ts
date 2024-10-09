/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__redis_cache__CustomPrivacyRequestField } from "./fides__api__schemas__redis_cache__CustomPrivacyRequestField";
import type { Identity } from "./Identity";
import type { PrivacyRequestSource } from "./PrivacyRequestSource";

/**
 * An extension of the base fides model with the addition of plus-only fields
 */
export type ConsentRequestCreateExtended = {
  identity: Identity;
  custom_privacy_request_fields?: Record<
    string,
    fides__api__schemas__redis_cache__CustomPrivacyRequestField
  > | null;
  property_id?: string | null;
  source?: PrivacyRequestSource | null;
};
