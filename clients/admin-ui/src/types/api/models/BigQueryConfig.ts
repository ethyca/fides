/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__connectors__models__KeyfileCreds } from "./fides__connectors__models__KeyfileCreds";

/**
 * The model for the connection config for BigQuery
 */
export type BigQueryConfig = {
  dataset?: string | null;
  keyfile_creds: fides__connectors__models__KeyfileCreds;
};
