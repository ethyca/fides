/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ResponseFormat } from "./ResponseFormat";
import type { StorageType } from "./StorageType";

/**
 * Storage Destination Response Schema
 */
export type StorageDestinationResponse = {
  name: string;
  type: StorageType;
  details: any;
  key: string;
  format: ResponseFormat;
  is_default?: boolean;
};
