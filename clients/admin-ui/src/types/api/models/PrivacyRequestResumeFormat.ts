/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__redis_cache__Identity } from "./fides__api__schemas__redis_cache__Identity";

/**
 * Expected request body to resume a privacy request after it was paused by a webhook
 */
export type PrivacyRequestResumeFormat = {
  derived_identity?: fides__api__schemas__redis_cache__Identity | null;
};
