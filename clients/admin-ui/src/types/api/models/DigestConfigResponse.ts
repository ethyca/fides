/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConditionGroup } from "./ConditionGroup";
import type { ConditionLeaf } from "./ConditionLeaf";
import type { DigestType } from "./DigestType";
import type { MessagingMethod } from "./MessagingMethod";

/**
 * Response schema for digest configurations.
 */
export type DigestConfigResponse = {
  /**
   * Digest configuration ID
   */
  id: string;
  /**
   * Digest configuration name
   */
  name: string;
  /**
   * Digest configuration description
   */
  description: string | null;
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
  messaging_service_type: MessagingMethod;
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
  config_metadata: null;
  /**
   * Digest conditions
   */
  conditions: Record<string, ConditionLeaf | ConditionGroup>;
  /**
   * Creation timestamp
   */
  created_at: string;
  /**
   * Last update timestamp
   */
  updated_at: string;
  /**
   * Last sent timestamp
   */
  last_sent_at: string | null;
  /**
   * Next scheduled timestamp
   */
  next_scheduled_at: string | null;
};
