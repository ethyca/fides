/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DownloadFormat } from "./DownloadFormat";
import type { StorageType } from "./StorageType";

/**
 * Storage Destination Response Schema
 */
export type StorageDestinationResponse = {
  name: string;
  type: StorageType;
  details: any;
  key: string;
  download_format: DownloadFormat;
  is_default?: boolean;
};
