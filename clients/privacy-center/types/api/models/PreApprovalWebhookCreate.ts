/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for creating/updating a Pre Approval Webhook
 */
export type PreApprovalWebhookCreate = {
  key?: string | null;
  name: string;
  connection_config_key: string;
};
