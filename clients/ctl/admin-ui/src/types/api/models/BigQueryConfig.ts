/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { KeyfileCreds } from './KeyfileCreds';

/**
 * The model for the connection config for BigQuery
 */
export type BigQueryConfig = {
  dataset?: string;
  keyfile_creds: KeyfileCreds;
};
