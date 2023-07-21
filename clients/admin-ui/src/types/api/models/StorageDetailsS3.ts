/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { S3AuthMethod } from "./S3AuthMethod";

/**
 * The details required to represent an AWS S3 storage bucket.
 */
export type StorageDetailsS3 = {
  naming?: string;
  auth_method: S3AuthMethod;
  bucket: string;
  max_retries?: number;
};
