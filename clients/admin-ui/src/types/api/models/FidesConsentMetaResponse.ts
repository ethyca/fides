/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMethod } from "./ConsentMethod";

/**
 * Fides metadata for the consent request.
 */
export type FidesConsentMetaResponse = {
  /**
   * User geography, from the request
   */
  geography?: string | null;
  /**
   * Method of consent preference
   */
  method?: ConsentMethod | null;
  /**
   * The request origin from the request headers
   */
  request_origin?: string | null;
  /**
   * Truncated IP address for reporting
   */
  truncated_ip_address?: string | null;
  /**
   * The referrer from the request headers
   */
  recorded_url?: string | null;
  /**
   * The user agent from the request headers
   */
  user_agent?: string | null;
  /**
   * The timestamp when consent was created in Fides
   */
  created_at: string;
};
