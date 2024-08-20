/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for updating a single webhook - fields are optional
 */
export type PreApprovalWebhookUpdate = {
  name?: string | null;
  connection_config_key?: string | null;
};
