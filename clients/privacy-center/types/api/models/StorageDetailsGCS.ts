/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GCSAuthMethod } from "./GCSAuthMethod";

/**
 * The details required to represent a Google Cloud Storage bucket.
 */
export type StorageDetailsGCS = {
  naming?: string;
  auth_method: GCSAuthMethod;
  bucket: string;
  max_retries?: number | null;
};
