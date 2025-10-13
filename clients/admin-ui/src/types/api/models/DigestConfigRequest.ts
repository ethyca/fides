/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DigestType } from "./DigestType";
import type { MessagingMethod } from "./MessagingMethod";

/**
 * Request schema for creating or updating digest configurations.
 */
export type DigestConfigRequest = {
  /**
   * Human-readable name for the digest configuration
   */
  name: string;
  /**
   * Optional description of the digest configuration
   */
  description?: string | null;
  /**
   * Digest type
   */
  digest_type: DigestType;
  /**
   * Whether digest notifications are enabled
   */
  enabled: boolean;
  /**
   * Type of messaging service (email, sms, etc.)
   */
  messaging_service_type?: MessagingMethod | null;
  /**
   * Cron expression for digest scheduling (default: weekly on Monday at 9 AM)
   */
  cron_expression: string;
  /**
   * Timezone for digest scheduling
   */
  timezone: string;
  /**
   * Additional configuration metadata (service-specific settings)
   */
  config_metadata?: null;
};
