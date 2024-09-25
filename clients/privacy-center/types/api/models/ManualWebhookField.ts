/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema to describe the attributes on a manual webhook field
 */
export type ManualWebhookField = {
  pii_field: string;
  dsr_package_label?: string | null;
  data_categories?: Array<string> | null;
};
