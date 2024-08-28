/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AdvancedSettings } from "./AdvancedSettings";

/**
 * EmailDocsSchema Secrets Schema for API Docs
 */
export type EmailDocsSchema = {
  third_party_vendor_name: string;
  recipient_email_address: string;
  test_email_address?: string | null;
  advanced_settings?: AdvancedSettings;
};
