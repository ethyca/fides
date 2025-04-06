/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PeriodicIntegrationFrequency } from "./PeriodicIntegrationFrequency";

/**
 * Datahub Schema for API docs.
 */
export type DatahubDocsSchema = {
  /**
   * The URL of your DataHub server.
   */
  datahub_server_url: string;
  /**
   * The token used to authenticate with your DataHub server.
   */
  datahub_token: string;
  /**
   * The frequency at which the integration should run. Available options are daily, weekly, and monthly.
   */
  frequency: PeriodicIntegrationFrequency;
  /**
   * The glossary node name to use on Datahub for Fides Data Categories. (e.g. FidesDataCategories)
   */
  glossary_node: string;
};
