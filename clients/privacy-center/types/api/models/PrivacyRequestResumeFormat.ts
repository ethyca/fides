/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Identity } from "./Identity";

/**
 * Expected request body to resume a privacy request after it was paused by a webhook
 */
export type PrivacyRequestResumeFormat = {
  derived_identity?: Identity | null;
};
