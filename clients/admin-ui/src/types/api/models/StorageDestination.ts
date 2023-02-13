/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ResponseFormat } from "./ResponseFormat";
import type { StorageDetailsLocal } from "./StorageDetailsLocal";
import type { StorageDetailsS3 } from "./StorageDetailsS3";
import type { StorageType } from "./StorageType";

/**
 * Storage Destination Schema
 */
export type StorageDestination = {
  name: string;
  type: StorageType;
  details: StorageDetailsS3 | StorageDetailsLocal;
  key?: string;
  format?: ResponseFormat;
};
