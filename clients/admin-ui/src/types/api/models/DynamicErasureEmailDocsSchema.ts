/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AdvancedSettings } from "./AdvancedSettings";
import type { FidesDatasetReference } from "./FidesDatasetReference";

/**
 * DynamicErasureEmailDocsSchema Secrets Schema for API Docs
 */
export type DynamicErasureEmailDocsSchema = {
  test_email_address?: string | null;
  advanced_settings?: AdvancedSettings;
  /**
   * Dataset reference to the field containing the third party vendor name. Both third_party_vendor_name and recipient_email_address must reference the same dataset and collection.
   */
  third_party_vendor_name: FidesDatasetReference;
  /**
   * Dataset reference to the field containing the recipient email address. Both third_party_vendor_name and recipient_email_address must reference the same dataset and collection.
   */
  recipient_email_address: FidesDatasetReference;
};
