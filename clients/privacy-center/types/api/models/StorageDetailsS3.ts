/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AWSAuthMethod } from "./AWSAuthMethod";

/**
 * The details required to represent an AWS S3 storage bucket.
 */
export type StorageDetailsS3 = {
  naming?: string;
  auth_method: AWSAuthMethod;
  bucket: string;
  max_retries?: number | null;
};
