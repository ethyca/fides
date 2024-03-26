/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__redis_cache__CustomPrivacyRequestField } from "./fides__api__schemas__redis_cache__CustomPrivacyRequestField";
import type { Identity } from "./Identity";

/**
 * Data required to create a consent PrivacyRequest
 */
export type ConsentRequestCreate = {
  identity: Identity;
  custom_privacy_request_fields?: Record<
    string,
    fides__api__schemas__redis_cache__CustomPrivacyRequestField
  >;
};
