/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CustomPrivacyRequestField } from "./CustomPrivacyRequestField";
import type { Identity } from "./Identity";

/**
 * Data required to create a consent PrivacyRequest
 */
export type ConsentRequestCreate = {
  identity: Identity;
  custom_privacy_request_fields?: Record<string, CustomPrivacyRequestField>;
};
