/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for asset responses
 */
export type Asset = {
  data_uses?: Array<string>;
  description?: string | null;
  name: string;
  asset_type: string;
  domain: string;
  page?: Array<string>;
  base_url?: string | null;
  locations?: Array<string>;
  id: string;
  system_id: string;
  parent?: Array<string>;
  parent_domain?: string | null;
  with_consent?: boolean;
};
