/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentStatus } from "./ConsentStatus";

export enum AssetType {
  COOKIE = "cookie",
  BROWSER_REQUEST = "browser_request",
  IFRAME = "iframe",
  JAVASCRIPT_TAG = "javascript_tag",
  IMAGE = "image",
}

/**
 * Schema for asset responses
 */
export type Asset = {
  data_uses?: Array<string>;
  description?: string | null;
  /**
   * Human-readable duration for which this asset persists (e.g., cookie lifetime)
   */
  duration?: string | null;
  name: string;
  asset_type: string;
  domain?: string | null;
  base_url?: string | null;
  locations?: Array<string>;
  id: string;
  system_id: string;
  parent?: Array<string>;
  parent_domain?: string | null;
  consent_status?: ConsentStatus;
  page?: Array<string>;
};
