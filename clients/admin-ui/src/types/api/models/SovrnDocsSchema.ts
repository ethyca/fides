/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AdvancedSettingsWithExtendedIdentityTypes } from "./AdvancedSettingsWithExtendedIdentityTypes";

/**
 * SovrnDocsSchema Secrets Schema for API Docs
 */
export type SovrnDocsSchema = {
  test_email_address?: string | null;
  advanced_settings?: AdvancedSettingsWithExtendedIdentityTypes;
  third_party_vendor_name?: string;
  recipient_email_address?: string;
};
