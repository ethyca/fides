/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ApplicationStatus } from "./ApplicationStatus";
import type { AuthenticationProtocol } from "./AuthenticationProtocol";
import type { VendorMatchConfidence } from "./VendorMatchConfidence";

/**
 * Application metadata from Identity Providers.
 *
 * Stored in StagedResource.meta JSONB column. Matches frontend OktaAppMetadata
 * interface for display in Action Center tables.
 */
export type IdentityProviderApplicationMetadata = {
  /**
   * Authentication protocol type
   */
  app_type?: AuthenticationProtocol | null;
  /**
   * Application lifecycle status
   */
  status?: ApplicationStatus | null;
  /**
   * ISO 8601 timestamp when application was created
   */
  created?: string | null;
  /**
   * SSO login URL
   */
  sign_on_url?: string | null;
  /**
   * Confidence level of vendor match from Compass service
   */
  vendor_match_confidence?: VendorMatchConfidence | null;
  /**
   * URL to vendor logo image from Compass service
   */
  vendor_logo_url?: string | null;
};
