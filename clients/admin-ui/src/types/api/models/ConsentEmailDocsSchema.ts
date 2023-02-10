/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AdvancedSettings } from "./AdvancedSettings";

/**
 * ConsentEmailDocsSchema Secrets Schema for API Docs
 */
export type ConsentEmailDocsSchema = {
  third_party_vendor_name: string;
  recipient_email_address: string;
  test_email_address?: string;
  advanced_settings: AdvancedSettings;
};
